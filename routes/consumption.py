from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, FoodItem, ConsumptionLog, Household
from datetime import datetime, date

consumption_bp = Blueprint('consumption', __name__)


@consumption_bp.route('/')
@login_required
def list_consumption_logs():
    # Get user's households
    households = Household.query.filter_by(user_id=current_user.id).all()
    
    if not households:
        flash('Please create a household first.', 'info')
        return redirect(url_for('household.create_household'))
    
    # Get selected household or use first one
    household_id = request.args.get('household_id', households[0].id, type=int)
    household = Household.query.filter_by(id=household_id, user_id=current_user.id).first_or_404()
    
    # Get consumption logs for this household
    food_item_ids = [item.id for item in household.food_items]
    consumption_logs = ConsumptionLog.query.filter(
        ConsumptionLog.food_item_id.in_(food_item_ids)
    ).order_by(ConsumptionLog.consumption_date.desc()).limit(100).all()
    
    return render_template('consumption/list.html', 
                         consumption_logs=consumption_logs,
                         household=household,
                         households=households)


@consumption_bp.route('/log', methods=['GET', 'POST'])
@login_required
def log_consumption():
    # Get user's households
    households = Household.query.filter_by(user_id=current_user.id).all()
    
    if not households:
        flash('Please create a household first.', 'info')
        return redirect(url_for('household.create_household'))
    
    # Get active food items
    household_id = request.args.get('household_id', households[0].id, type=int)
    household = Household.query.filter_by(id=household_id, user_id=current_user.id).first()
    
    if household:
        active_items = FoodItem.query.filter_by(
            household_id=household.id, 
            status='Active'
        ).all()
    else:
        active_items = []
    
    if request.method == 'POST':
        food_item_id = request.form.get('food_item_id', type=int)
        quantity_consumed = request.form.get('quantity_consumed')
        consumption_date = request.form.get('consumption_date')
        notes = request.form.get('notes', '').strip()
        
        # Validation
        errors = []
        
        food_item = FoodItem.query.get(food_item_id)
        if not food_item or food_item.household.user_id != current_user.id:
            errors.append('Please select a valid food item.')
        
        try:
            quantity_consumed = float(quantity_consumed)
            if quantity_consumed <= 0:
                raise ValueError("Quantity must be positive")
            if food_item and quantity_consumed > float(food_item.quantity):
                errors.append(f'Consumed quantity cannot exceed available quantity ({food_item.quantity} {food_item.unit}).')
        except (ValueError, TypeError):
            errors.append('Please provide a valid quantity consumed.')
        
        try:
            consumption_date = datetime.strptime(consumption_date, '%Y-%m-%d').date()
            if consumption_date > date.today():
                errors.append('Consumption date cannot be in the future.')
            if food_item and consumption_date < food_item.purchase_date:
                errors.append('Consumption date cannot be before purchase date.')
        except (ValueError, TypeError):
            errors.append('Please provide a valid consumption date.')
        
        if errors:
            for error in errors:
                flash(error, 'warning')
            return render_template('consumption/log.html', 
                                 households=households,
                                 active_items=active_items,
                                 selected_household=household_id)
        
        # Create consumption log
        try:
            consumption_log = ConsumptionLog(
                food_item_id=food_item.id,
                consumption_date=consumption_date,
                quantity_consumed=quantity_consumed,
                notes=notes
            )
            db.session.add(consumption_log)
            
            # Update food item quantity
            food_item.quantity = float(food_item.quantity) - quantity_consumed
            
            # If quantity reaches zero, mark as consumed
            if food_item.quantity <= 0:
                food_item.status = 'Consumed'
                food_item.quantity = 0
            
            db.session.commit()
            
            flash(f'Consumption logged successfully for "{food_item.item_name}"!', 'success')
            return redirect(url_for('consumption.list_consumption_logs', household_id=household_id))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while logging consumption.', 'danger')
            print(f"Consumption logging error: {e}")
    
    return render_template('consumption/log.html', 
                         households=households,
                         active_items=active_items,
                         selected_household=household_id)


@consumption_bp.route('/<int:log_id>/delete', methods=['POST'])
@login_required
def delete_consumption_log(log_id):
    consumption_log = ConsumptionLog.query.get_or_404(log_id)
    
    # Verify ownership
    if consumption_log.food_item.household.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('consumption.list_consumption_logs'))
    
    try:
        # Restore quantity to food item
        food_item = consumption_log.food_item
        food_item.quantity = float(food_item.quantity) + float(consumption_log.quantity_consumed)
        
        # If item was marked as consumed, reactivate it
        if food_item.status == 'Consumed':
            food_item.status = 'Active'
        
        db.session.delete(consumption_log)
        db.session.commit()
        
        flash('Consumption log deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the consumption log.', 'danger')
        print(f"Consumption log deletion error: {e}")
    
    return redirect(url_for('consumption.list_consumption_logs'))


@consumption_bp.route('/quick_log/<int:item_id>', methods=['POST'])
@login_required
def quick_log(item_id):
    """Quick consumption logging from food list page"""
    food_item = FoodItem.query.get_or_404(item_id)
    
    # Verify ownership
    if food_item.household.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('food.list_food_items'))
    
    quantity_consumed = request.form.get('quantity_consumed')
    
    try:
        quantity_consumed = float(quantity_consumed)
        if quantity_consumed <= 0 or quantity_consumed > float(food_item.quantity):
            raise ValueError("Invalid quantity")
        
        # Create consumption log
        consumption_log = ConsumptionLog(
            food_item_id=food_item.id,
            consumption_date=date.today(),
            quantity_consumed=quantity_consumed
        )
        db.session.add(consumption_log)
        
        # Update food item quantity
        food_item.quantity = float(food_item.quantity) - quantity_consumed
        
        if food_item.quantity <= 0:
            food_item.status = 'Consumed'
            food_item.quantity = 0
        
        db.session.commit()
        flash('Consumption logged successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Invalid quantity or error logging consumption.', 'danger')
        print(f"Quick log error: {e}")
    
    return redirect(url_for('food.list_food_items'))