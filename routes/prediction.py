from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, FoodItem, Household, Alert, Recommendation, WasteRecord, FoodCategory
from utils.waste_predictor import WastePredictor
from utils.recommender import WasteReductionRecommender
from sqlalchemy import func, extract
from datetime import datetime, date, timedelta
import json

prediction_bp = Blueprint('prediction', __name__)


@prediction_bp.route('/dashboard')
@login_required
def dashboard():
    # Get user's households
    households = Household.query.filter_by(user_id=current_user.id).all()
    
    if not households:
        flash('Please create a household first to get started.', 'info')
        return redirect(url_for('household.create_household'))
    
    # Get selected household or use first one
    household_id = request.args.get('household_id', households[0].id, type=int)
    household = Household.query.filter_by(id=household_id, user_id=current_user.id).first_or_404()
    
    # Get dashboard statistics
    active_items = FoodItem.query.filter_by(household_id=household.id, status='Active').all()
    
    total_items = len(active_items)
    high_risk_items = [item for item in active_items if float(item.waste_risk_score) >= 70]
    medium_risk_items = [item for item in active_items if 40 <= float(item.waste_risk_score) < 70]
    expiring_soon = [item for item in active_items if item.days_until_expiry is not None and 0 <= item.days_until_expiry <= 3]
    
    # Get recent waste records
    recent_waste = WasteRecord.query.filter_by(household_id=household.id)\
        .order_by(WasteRecord.waste_date.desc()).limit(5).all()
    
    total_waste_count = WasteRecord.query.filter_by(household_id=household.id).count()
    total_waste_value = db.session.query(func.sum(WasteRecord.estimated_value))\
        .filter_by(household_id=household.id).scalar() or 0
    
    # Get unread alerts
    unread_alerts = Alert.query.filter_by(household_id=household.id, is_read=False)\
        .order_by(Alert.created_at.desc()).limit(10).all()
    
    stats = {
        'total_items': total_items,
        'high_risk_count': len(high_risk_items),
        'medium_risk_count': len(medium_risk_items),
        'expiring_soon_count': len(expiring_soon),
        'total_waste_count': total_waste_count,
        'total_waste_value': float(total_waste_value),
        'unread_alerts_count': len(unread_alerts)
    }
    
    return render_template('dashboard.html',
                         household=household,
                         households=households,
                         stats=stats,
                         high_risk_items=high_risk_items[:5],
                         expiring_soon=expiring_soon[:5],
                         recent_waste=recent_waste,
                         unread_alerts=unread_alerts)


@prediction_bp.route('/calculate_risk/<int:household_id>')
@login_required
def calculate_risk(household_id):
    """Calculate waste risk for all active items in a household"""
    household = Household.query.filter_by(id=household_id, user_id=current_user.id).first_or_404()
    
    active_items = FoodItem.query.filter_by(household_id=household.id, status='Active').all()
    
    updated_count = 0
    alerts_created = 0
    
    try:
        for item in active_items:
            # Calculate risk score
            risk_score = WastePredictor.calculate_waste_risk(item)
            item.waste_risk_score = risk_score
            updated_count += 1
            
            # Generate alerts if needed
            if WastePredictor.should_generate_alert(item):
                # Check if alert already exists
                existing_alert = Alert.query.filter_by(
                    food_item_id=item.id,
                    is_read=False
                ).first()
                
                if not existing_alert:
                    alert_type = 'Expired' if item.days_until_expiry < 0 else \
                                'Expiring Soon' if item.days_until_expiry <= 3 else \
                                'High Risk' if risk_score >= 70 else 'Medium Risk'
                    
                    alert = Alert(
                        food_item_id=item.id,
                        household_id=household.id,
                        alert_type=alert_type,
                        alert_message=WasteReductionRecommender.get_alert_message(item),
                        recommendation='; '.join([r['text'] for r in WasteReductionRecommender.generate_recommendations(item)[:2]])
                    )
                    db.session.add(alert)
                    alerts_created += 1
        
        db.session.commit()
        flash(f'Risk calculated for {updated_count} items. {alerts_created} new alerts generated.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while calculating risk scores.', 'danger')
        print(f"Risk calculation error: {e}")
    
    return redirect(url_for('prediction.dashboard', household_id=household_id))


@prediction_bp.route('/alerts')
@login_required
def list_alerts():
    households = Household.query.filter_by(user_id=current_user.id).all()
    
    if not households:
        flash('Please create a household first.', 'info')
        return redirect(url_for('household.create_household'))
    
    household_id = request.args.get('household_id', households[0].id, type=int)
    household = Household.query.filter_by(id=household_id, user_id=current_user.id).first_or_404()
    
    show_read = request.args.get('show_read', 'false') == 'true'
    
    if show_read:
        alerts = Alert.query.filter_by(household_id=household.id)\
            .order_by(Alert.created_at.desc()).all()
    else:
        alerts = Alert.query.filter_by(household_id=household.id, is_read=False)\
            .order_by(Alert.created_at.desc()).all()
    
    return render_template('alerts.html',
                         alerts=alerts,
                         household=household,
                         households=households,
                         show_read=show_read)


@prediction_bp.route('/alerts/<int:alert_id>/mark_read', methods=['POST'])
@login_required
def mark_alert_read(alert_id):
    alert = Alert.query.get_or_404(alert_id)
    
    if alert.household.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('prediction.list_alerts'))
    
    try:
        alert.is_read = True
        db.session.commit()
        flash('Alert marked as read.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred.', 'danger')
        print(f"Alert update error: {e}")
    
    return redirect(url_for('prediction.list_alerts'))


@prediction_bp.route('/analytics')
@login_required
def analytics():
    households = Household.query.filter_by(user_id=current_user.id).all()
    
    if not households:
        flash('Please create a household first.', 'info')
        return redirect(url_for('household.create_household'))
    
    household_id = request.args.get('household_id', households[0].id, type=int)
    household = Household.query.filter_by(id=household_id, user_id=current_user.id).first_or_404()
    
    # Waste by category
    waste_by_category = db.session.query(
        FoodCategory.category_name,
        func.count(WasteRecord.id).label('count'),
        func.sum(WasteRecord.quantity_wasted).label('total_quantity')
    ).join(FoodItem, WasteRecord.food_item_id == FoodItem.id)\
     .join(FoodCategory, FoodItem.category_id == FoodCategory.id)\
     .filter(WasteRecord.household_id == household.id)\
     .group_by(FoodCategory.category_name)\
     .all()
    
    # Monthly waste trend (last 6 months)
    six_months_ago = date.today() - timedelta(days=180)
    monthly_waste = db.session.query(
        extract('year', WasteRecord.waste_date).label('year'),
        extract('month', WasteRecord.waste_date).label('month'),
        func.count(WasteRecord.id).label('count'),
        func.sum(WasteRecord.estimated_value).label('value')
    ).filter(
        WasteRecord.household_id == household.id,
        WasteRecord.waste_date >= six_months_ago
    ).group_by('year', 'month')\
     .order_by('year', 'month')\
     .all()
    
    # Waste by reason
    waste_by_reason = db.session.query(
        WasteRecord.waste_reason,
        func.count(WasteRecord.id).label('count')
    ).filter(WasteRecord.household_id == household.id)\
     .group_by(WasteRecord.waste_reason)\
     .all()
    
    # Current inventory status
    inventory_status = db.session.query(
        FoodItem.status,
        func.count(FoodItem.id).label('count')
    ).filter(FoodItem.household_id == household.id)\
     .group_by(FoodItem.status)\
     .all()
    
    return render_template('analytics.html',
                         household=household,
                         households=households,
                         waste_by_category=waste_by_category,
                         monthly_waste=monthly_waste,
                         waste_by_reason=waste_by_reason,
                         inventory_status=inventory_status)


@prediction_bp.route('/recommendations/<int:item_id>')
@login_required
def view_recommendations(item_id):
    food_item = FoodItem.query.get_or_404(item_id)
    
    if food_item.household.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('prediction.dashboard'))
    
    recommendations = WasteReductionRecommender.generate_recommendations(food_item)
    general_tips = WasteReductionRecommender.get_general_tips()
    
    return render_template('recommendations.html',
                         food_item=food_item,
                         recommendations=recommendations,
                         general_tips=general_tips)