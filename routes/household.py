from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Household

household_bp = Blueprint('household', __name__)


@household_bp.route('/')
@login_required
def list_households():
    households = Household.query.filter_by(user_id=current_user.id).all()
    return render_template('household/list.html', households=households)


@household_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_household():
    if request.method == 'POST':
        household_name = request.form.get('household_name', '').strip()
        num_members = request.form.get('num_members', 1)
        location = request.form.get('location', '').strip()
        
        # Validation
        if not household_name:
            flash('Household name is required.', 'warning')
            return render_template('household/create.html')
        
        try:
            num_members = int(num_members)
            if num_members < 1:
                raise ValueError("Number of members must be at least 1")
        except ValueError:
            flash('Please provide a valid number of members.', 'warning')
            return render_template('household/create.html')
        
        # Create household
        try:
            household = Household(
                user_id=current_user.id,
                household_name=household_name,
                num_members=num_members,
                location=location
            )
            db.session.add(household)
            db.session.commit()
            flash(f'Household "{household_name}" created successfully!', 'success')
            return redirect(url_for('household.list_households'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating the household.', 'danger')
            print(f"Household creation error: {e}")
    
    return render_template('household/create.html')


@household_bp.route('/<int:household_id>')
@login_required
def view_household(household_id):
    household = Household.query.filter_by(id=household_id, user_id=current_user.id).first_or_404()
    
    # Get statistics
    total_items = len([item for item in household.food_items if item.status == 'Active'])
    total_waste = len(household.waste_records)
    high_risk_items = len([item for item in household.food_items 
                          if item.status == 'Active' and float(item.waste_risk_score) > 70])
    
    stats = {
        'total_items': total_items,
        'total_waste': total_waste,
        'high_risk_items': high_risk_items
    }
    
    return render_template('household/view.html', household=household, stats=stats)


@household_bp.route('/<int:household_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_household(household_id):
    household = Household.query.filter_by(id=household_id, user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        household_name = request.form.get('household_name', '').strip()
        num_members = request.form.get('num_members', 1)
        location = request.form.get('location', '').strip()
        
        # Validation
        if not household_name:
            flash('Household name is required.', 'warning')
            return render_template('household/edit.html', household=household)
        
        try:
            num_members = int(num_members)
            if num_members < 1:
                raise ValueError("Number of members must be at least 1")
        except ValueError:
            flash('Please provide a valid number of members.', 'warning')
            return render_template('household/edit.html', household=household)
        
        # Update household
        try:
            household.household_name = household_name
            household.num_members = num_members
            household.location = location
            db.session.commit()
            flash('Household updated successfully!', 'success')
            return redirect(url_for('household.view_household', household_id=household.id))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the household.', 'danger')
            print(f"Household update error: {e}")
    
    return render_template('household/edit.html', household=household)


@household_bp.route('/<int:household_id>/delete', methods=['POST'])
@login_required
def delete_household(household_id):
    household = Household.query.filter_by(id=household_id, user_id=current_user.id).first_or_404()
    
    try:
        household_name = household.household_name
        db.session.delete(household)
        db.session.commit()
        flash(f'Household "{household_name}" deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the household.', 'danger')
        print(f"Household deletion error: {e}")
    
    return redirect(url_for('household.list_households'))