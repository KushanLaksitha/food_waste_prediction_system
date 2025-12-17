from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, FoodItem, Household, FoodCategory, WasteRecord
from datetime import datetime, date

food_bp = Blueprint('food', __name__)


@food_bp.route('/')
@login_required
def list_food_items():
    # Get user's households
    households = Household.query.filter_by(user_id=current_user.id).all()
    
    if not households:
        flash('Please create a household first.', 'info')
        return redirect(url_for('household.create_household'))
    
    # Get selected household or use first one
    household_id = request.args.get('household_id', households[0].id, type=int)
    household = Household.query.filter_by(id=household_id, user_id=current_user.id).first_or_404()
    
    # Get filter parameters
    status = request.args.get('status', 'Active')
    category_id = request.args.get('category_id', type=int)
    
    # Build query
    query = FoodItem.query.filter_by(household_id=household.id)
    
    if status != 'All':
        query = query.filter_by(status=status)
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    food_items = query.order_by(FoodItem.expiry_date.asc()).all()
    categories = FoodCategory.query.all()
    
    return render_template('food/list.html', 
                         food_items=food_items, 
                         household=household,
                         households=households,
                         categories=categories,
                         selected_status=status,
                         selected_category=category_id)


@food_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_food_item():
    households = Household.query.filter_by(user_id=current_user.id).all()
    
    if not households:
        flash('Please create a household first.', 'info')
        return redirect(url_for('household.create_household'))
    
    categories = FoodCategory.query.all()
    
    if request.method == 'POST':
        household_id = request.form.get('household_id', type=int)
        category_id = request.form.get('category_id', type=int)
        item_name = request.form.get('item_name', '').strip()
        quantity = request.form.get('quantity')
        unit = request.form.get('unit', '').strip()
        purchase_date = request.form.get('purchase_date')
        expiry_date = request.form.get('expiry_date')
        
        # Validation
        errors = []
        
        if not household_id or not Household.query.filter_by(id=household_id, user_id=current_user.id).first():
            errors.append('Please select a valid household.')
        
        if not category_id or not FoodCategory.query.get(category_id):
            errors.append('Please select a valid category.')
        
        if not item_name:
            errors.append('Item name is required.')
        
        try:
            quantity = float(quantity)
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
        except (ValueError, TypeError):
            errors.append('Please provide a valid quantity.')
        
        if not unit:
            errors.append('Unit is required.')
        
        try:
            purchase_date = datetime.strptime(purchase_date, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            errors.append('Please provide a valid purchase date.')
        
        try:
            expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()
            if expiry_date <= purchase_date:
                errors.append('Expiry date must be after purchase date.')
        except (ValueError, TypeError):
            errors.append('Please provide a valid expiry date.')
        
        if errors:
            for error in errors:
                flash(error, 'warning')
            return render_template('food/add.html', households=households, categories=categories)
        
        # Create food item
        try:
            food_item = FoodItem(
                household_id=household_id,
                category_id=category_id,
                item_name=item_name,
                quantity=quantity,
                unit=unit,
                purchase_date=purchase_date,
                expiry_date=expiry_date,
                initial_quantity=quantity,
                status='Active'
            )
            db.session.add(food_item)
            db.session.commit()
            
            flash(f'Food item "{item_name}" added successfully!', 'success')
            return redirect(url_for('food.list_food_items'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while adding the food item.', 'danger')
            print(f"Food item creation error: {e}")
    
    return render_template('food/add.html', households=households, categories=categories)


@food_bp.route('/<int:item_id>')
@login_required
def view_food_item(item_id):
    food_item = FoodItem.query.get_or_404(item_id)
    
    # Verify ownership
    if food_item.household.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('food.list_food_items'))
    
    return render_template('food/view.html', food_item=food_item)


@food_bp.route('/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_food_item(item_id):
    food_item = FoodItem.query.get_or_404(item_id)
    
    # Verify ownership
    if food_item.household.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('food.list_food_items'))
    
    categories = FoodCategory.query.all()
    
    if request.method == 'POST':
        category_id = request.form.get('category_id', type=int)
        item_name = request.form.get('item_name', '').strip()
        quantity = request.form.get('quantity')
        unit = request.form.get('unit', '').strip()
        expiry_date = request.form.get('expiry_date')
        
        # Validation
        errors = []
        
        if not category_id or not FoodCategory.query.get(category_id):
            errors.append('Please select a valid category.')
        
        if not item_name:
            errors.append('Item name is required.')
        
        try:
            quantity = float(quantity)
            if quantity < 0:
                raise ValueError("Quantity cannot be negative")
        except (ValueError, TypeError):
            errors.append('Please provide a valid quantity.')
        
        if not unit:
            errors.append('Unit is required.')
        
        try:
            expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            errors.append('Please provide a valid expiry date.')
        
        if errors:
            for error in errors:
                flash(error, 'warning')
            return render_template('food/edit.html', food_item=food_item, categories=categories)
        
        # Update food item
        try:
            food_item.category_id = category_id
            food_item.item_name = item_name
            food_item.quantity = quantity
            food_item.unit = unit
            food_item.expiry_date = expiry_date
            db.session.commit()
            
            flash('Food item updated successfully!', 'success')
            return redirect(url_for('food.view_food_item', item_id=food_item.id))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the food item.', 'danger')
            print(f"Food item update error: {e}")
    
    return render_template('food/edit.html', food_item=food_item, categories=categories)


@food_bp.route('/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_food_item(item_id):
    food_item = FoodItem.query.get_or_404(item_id)
    
    # Verify ownership
    if food_item.household.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('food.list_food_items'))
    
    try:
        item_name = food_item.item_name
        db.session.delete(food_item)
        db.session.commit()
        flash(f'Food item "{item_name}" deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the food item.', 'danger')
        print(f"Food item deletion error: {e}")
    
    return redirect(url_for('food.list_food_items'))


@food_bp.route('/<int:item_id>/mark_wasted', methods=['POST'])
@login_required
def mark_wasted(item_id):
    food_item = FoodItem.query.get_or_404(item_id)
    
    # Verify ownership
    if food_item.household.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('food.list_food_items'))
    
    waste_reason = request.form.get('waste_reason', 'Other')
    estimated_value = request.form.get('estimated_value', 0)
    notes = request.form.get('notes', '').strip()
    
    try:
        estimated_value = float(estimated_value) if estimated_value else 0
    except ValueError:
        estimated_value = 0
    
    try:
        # Create waste record
        waste_record = WasteRecord(
            food_item_id=food_item.id,
            household_id=food_item.household_id,
            waste_date=date.today(),
            quantity_wasted=food_item.quantity,
            waste_reason=waste_reason,
            estimated_value=estimated_value,
            notes=notes
        )
        db.session.add(waste_record)
        
        # Update food item status
        food_item.status = 'Wasted'
        food_item.quantity = 0
        
        db.session.commit()
        flash('Food item marked as wasted.', 'info')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while recording the waste.', 'danger')
        print(f"Waste recording error: {e}")
    
    return redirect(url_for('food.list_food_items'))