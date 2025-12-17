from datetime import datetime, date
from models import FoodItem, FoodCategory


class WastePredictor:
    """
    Calculates waste risk scores for food items based on multiple factors:
    - Remaining shelf life
    - Consumption frequency
    - Quantity remaining
    - Perishability level
    """
    
    # Weight factors for risk calculation
    SHELF_LIFE_WEIGHT = 0.40
    CONSUMPTION_WEIGHT = 0.30
    QUANTITY_WEIGHT = 0.20
    PERISHABILITY_WEIGHT = 0.10
    
    @staticmethod
    def calculate_waste_risk(food_item):
        """
        Calculate overall waste risk score (0-100)
        Higher score means higher risk of waste
        """
        if food_item.status != 'Active':
            return 0
        
        # Calculate individual risk factors
        shelf_life_risk = WastePredictor._calculate_shelf_life_risk(food_item)
        consumption_risk = WastePredictor._calculate_consumption_risk(food_item)
        quantity_risk = WastePredictor._calculate_quantity_risk(food_item)
        perishability_risk = WastePredictor._calculate_perishability_risk(food_item)
        
        # Calculate weighted risk score
        risk_score = (
            shelf_life_risk * WastePredictor.SHELF_LIFE_WEIGHT +
            consumption_risk * WastePredictor.CONSUMPTION_WEIGHT +
            quantity_risk * WastePredictor.QUANTITY_WEIGHT +
            perishability_risk * WastePredictor.PERISHABILITY_WEIGHT
        )
        
        return min(100, max(0, risk_score))
    
    @staticmethod
    def _calculate_shelf_life_risk(food_item):
        """
        Calculate risk based on remaining shelf life
        Returns: 0-100 score
        """
        days_until_expiry = food_item.days_until_expiry
        
        if days_until_expiry is None:
            return 50  # Default medium risk
        
        # Already expired
        if days_until_expiry < 0:
            return 100
        
        # Critical zone (0-2 days)
        if days_until_expiry <= 2:
            return 90
        
        # High risk zone (3-5 days)
        if days_until_expiry <= 5:
            return 70
        
        # Medium risk zone (6-10 days)
        if days_until_expiry <= 10:
            return 50
        
        # Low risk zone (11-20 days)
        if days_until_expiry <= 20:
            return 30
        
        # Very low risk (>20 days)
        return 10
    
    @staticmethod
    def _calculate_consumption_risk(food_item):
        """
        Calculate risk based on consumption patterns
        Returns: 0-100 score
        """
        consumption_rate = food_item.consumption_rate
        remaining_quantity = float(food_item.quantity)
        days_until_expiry = food_item.days_until_expiry
        
        if days_until_expiry is None or days_until_expiry <= 0:
            return 100
        
        # No consumption history
        if consumption_rate == 0:
            # Check if item is old
            days_since_purchase = (date.today() - food_item.purchase_date).days
            if days_since_purchase > 3:
                return 80  # High risk - not being consumed
            return 50  # Medium risk - recently purchased
        
        # Calculate days needed to consume remaining quantity
        days_to_consume = remaining_quantity / consumption_rate if consumption_rate > 0 else 999
        
        # Will it be consumed before expiry?
        if days_to_consume > days_until_expiry * 1.5:
            return 90  # Very high risk
        elif days_to_consume > days_until_expiry:
            return 70  # High risk
        elif days_to_consume > days_until_expiry * 0.8:
            return 50  # Medium risk
        else:
            return 20  # Low risk - good consumption rate
    
    @staticmethod
    def _calculate_quantity_risk(food_item):
        """
        Calculate risk based on remaining quantity vs initial quantity
        Returns: 0-100 score
        """
        remaining_quantity = float(food_item.quantity)
        initial_quantity = float(food_item.initial_quantity)
        
        if initial_quantity == 0:
            return 0
        
        percentage_remaining = (remaining_quantity / initial_quantity) * 100
        
        # High percentage remaining = higher risk
        if percentage_remaining > 80:
            return 70
        elif percentage_remaining > 60:
            return 50
        elif percentage_remaining > 40:
            return 30
        elif percentage_remaining > 20:
            return 15
        else:
            return 5
    
    @staticmethod
    def _calculate_perishability_risk(food_item):
        """
        Calculate risk based on food category perishability
        Returns: 0-100 score
        """
        perishability_level = food_item.category.perishability_level
        
        if perishability_level == 'High':
            return 80
        elif perishability_level == 'Medium':
            return 50
        else:  # Low
            return 20
    
    @staticmethod
    def get_risk_level(risk_score):
        """
        Convert risk score to categorical risk level
        """
        if risk_score >= 70:
            return 'High'
        elif risk_score >= 40:
            return 'Medium'
        else:
            return 'Low'
    
    @staticmethod
    def get_risk_color(risk_score):
        """
        Get color code for risk level (for UI display)
        """
        if risk_score >= 70:
            return 'danger'  # Red
        elif risk_score >= 40:
            return 'warning'  # Yellow
        else:
            return 'success'  # Green
    
    @staticmethod
    def should_generate_alert(food_item, threshold=40):
        """
        Determine if an alert should be generated for this item
        """
        risk_score = float(food_item.waste_risk_score)
        days_until_expiry = food_item.days_until_expiry
        
        # Generate alert if:
        # 1. Risk score exceeds threshold
        # 2. Item is expiring soon (within 3 days)
        # 3. Item has expired
        
        if risk_score >= threshold:
            return True
        
        if days_until_expiry is not None:
            if days_until_expiry <= 3:
                return True
            if days_until_expiry < 0:
                return True
        
        return False