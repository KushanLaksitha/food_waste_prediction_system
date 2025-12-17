from models import FoodItem


class WasteReductionRecommender:
    """
    Generates personalized recommendations for reducing food waste
    based on food item characteristics and risk level
    """
    
    # Preservation methods by category
    PRESERVATION_METHODS = {
        'Vegetables': [
            'Store in crisper drawer with proper humidity',
            'Blanch and freeze for long-term storage',
            'Make vegetable soup or stir-fry',
            'Pickle or ferment for extended shelf life'
        ],
        'Fruits': [
            'Freeze for smoothies or baking',
            'Make fruit jam or compote',
            'Dehydrate for fruit chips',
            'Store separately from ethylene-sensitive items'
        ],
        'Dairy': [
            'Freeze milk, cheese, or butter',
            'Make yogurt or cheese',
            'Use in baking or cooking',
            'Store in coldest part of refrigerator'
        ],
        'Meat': [
            'Freeze immediately if not using soon',
            'Cook and refrigerate for meal prep',
            'Marinate for extended flavor and life',
            'Store in coldest part of refrigerator'
        ],
        'Fish': [
            'Freeze immediately if not using within 24 hours',
            'Cook and use in salads or pasta',
            'Smoke or cure for preservation',
            'Store on ice in refrigerator'
        ],
        'Bread & Bakery': [
            'Freeze sliced bread for freshness',
            'Make bread crumbs or croutons',
            'Toast or make French toast',
            'Store in paper bag at room temperature'
        ],
        'Grains': [
            'Store in airtight containers',
            'Keep in cool, dry place',
            'Cook in batches for meal prep',
            'Check for moisture or pests regularly'
        ]
    }
    
    # Recipe suggestions by category
    RECIPE_SUGGESTIONS = {
        'Vegetables': [
            'Vegetable stir-fry with rice',
            'Mixed vegetable curry',
            'Vegetable soup',
            'Roasted vegetable medley',
            'Vegetable fried rice'
        ],
        'Fruits': [
            'Fruit smoothie',
            'Fruit salad',
            'Baked fruit dessert',
            'Fresh fruit juice',
            'Fruit yogurt parfait'
        ],
        'Dairy': [
            'Cheese omelette',
            'Creamy pasta sauce',
            'Homemade ice cream',
            'Yogurt-based smoothie',
            'Cheese-stuffed dishes'
        ],
        'Meat': [
            'Stir-fried meat with vegetables',
            'Meat curry',
            'Grilled meat skewers',
            'Meat fried rice',
            'Meat soup'
        ],
        'Bread & Bakery': [
            'French toast',
            'Bread pudding',
            'Garlic bread',
            'Sandwiches',
            'Bread pizza'
        ]
    }
    
    @staticmethod
    def generate_recommendations(food_item):
        """
        Generate comprehensive recommendations for a food item
        Returns list of recommendation dictionaries
        """
        recommendations = []
        risk_score = float(food_item.waste_risk_score)
        days_until_expiry = food_item.days_until_expiry
        category_name = food_item.category.category_name
        
        # Critical recommendations for high-risk items
        if risk_score >= 70 or (days_until_expiry is not None and days_until_expiry <= 3):
            recommendations.extend(
                WasteReductionRecommender._get_urgent_recommendations(food_item)
            )
        
        # Medium-risk recommendations
        elif risk_score >= 40 or (days_until_expiry is not None and days_until_expiry <= 7):
            recommendations.extend(
                WasteReductionRecommender._get_medium_risk_recommendations(food_item)
            )
        
        # Low-risk recommendations
        else:
            recommendations.extend(
                WasteReductionRecommender._get_low_risk_recommendations(food_item)
            )
        
        # Add preservation methods
        if category_name in WasteReductionRecommender.PRESERVATION_METHODS:
            preservation = {
                'type': 'Preserve',
                'priority': 2,
                'text': f"Preservation options: {', '.join(WasteReductionRecommender.PRESERVATION_METHODS[category_name][:2])}"
            }
            recommendations.append(preservation)
        
        # Add recipe suggestions
        if category_name in WasteReductionRecommender.RECIPE_SUGGESTIONS:
            recipes = WasteReductionRecommender.RECIPE_SUGGESTIONS[category_name][:2]
            recipe = {
                'type': 'Recipe Suggestion',
                'priority': 3,
                'text': f"Try making: {' or '.join(recipes)}"
            }
            recommendations.append(recipe)
        
        return recommendations
    
    @staticmethod
    def _get_urgent_recommendations(food_item):
        """Generate recommendations for high-risk items"""
        recommendations = []
        days_until_expiry = food_item.days_until_expiry
        
        if days_until_expiry is not None and days_until_expiry < 0:
            recommendations.append({
                'type': 'Use Soon',
                'priority': 1,
                'text': f'⚠️ EXPIRED: Check if {food_item.item_name} is still safe. If spoiled, dispose immediately.'
            })
        elif days_until_expiry is not None and days_until_expiry <= 1:
            recommendations.append({
                'type': 'Use Soon',
                'priority': 1,
                'text': f'🚨 USE TODAY: {food_item.item_name} expires in {days_until_expiry} day(s). Use immediately or freeze.'
            })
        elif days_until_expiry is not None and days_until_expiry <= 3:
            recommendations.append({
                'type': 'Use Soon',
                'priority': 1,
                'text': f'⚡ URGENT: Use {food_item.item_name} within {days_until_expiry} days or preserve it.'
            })
        else:
            recommendations.append({
                'type': 'Use Soon',
                'priority': 1,
                'text': f'⚠️ HIGH RISK: {food_item.item_name} is at high risk of waste. Use soon or consider donating.'
            })
        
        # Suggest donation if quantity is high
        if float(food_item.quantity) > float(food_item.initial_quantity) * 0.5:
            recommendations.append({
                'type': 'Donate',
                'priority': 1,
                'text': f'Consider donating excess {food_item.item_name} to reduce waste.'
            })
        
        return recommendations
    
    @staticmethod
    def _get_medium_risk_recommendations(food_item):
        """Generate recommendations for medium-risk items"""
        recommendations = []
        days_until_expiry = food_item.days_until_expiry
        
        if days_until_expiry is not None:
            recommendations.append({
                'type': 'Use Soon',
                'priority': 2,
                'text': f'📅 Plan to use {food_item.item_name} within {days_until_expiry} days.'
            })
        
        # Check consumption rate
        if food_item.consumption_rate == 0:
            recommendations.append({
                'type': 'Use Soon',
                'priority': 2,
                'text': f'⏰ Start using {food_item.item_name} - no consumption recorded yet.'
            })
        elif food_item.consumption_rate < 0.1:
            recommendations.append({
                'type': 'Use Soon',
                'priority': 2,
                'text': f'🐌 Slow consumption rate for {food_item.item_name}. Increase usage frequency.'
            })
        
        return recommendations
    
    @staticmethod
    def _get_low_risk_recommendations(food_item):
        """Generate recommendations for low-risk items"""
        recommendations = []
        
        recommendations.append({
            'type': 'Use Soon',
            'priority': 3,
            'text': f'✅ {food_item.item_name} is being consumed well. Continue current usage pattern.'
        })
        
        return recommendations
    
    @staticmethod
    def get_general_tips():
        """Get general food waste reduction tips"""
        return [
            'Store food properly: Keep fruits and vegetables in appropriate conditions',
            'Practice FIFO: First In, First Out - use older items first',
            'Plan meals: Create weekly meal plans based on what you have',
            'Proper portions: Cook appropriate quantities to avoid leftovers',
            'Smart shopping: Buy only what you need and check inventory first',
            'Understand dates: "Best before" vs "Use by" - know the difference',
            'Freeze extras: Freeze portions you won\'t use immediately',
            'Get creative: Use leftovers in new recipes',
            'Compost: If food waste is unavoidable, compost when possible',
            'Donate: Share excess food with community or food banks'
        ]
    
    @staticmethod
    def get_alert_message(food_item):
        """Generate alert message for a food item"""
        risk_score = float(food_item.waste_risk_score)
        days_until_expiry = food_item.days_until_expiry
        
        if days_until_expiry is not None and days_until_expiry < 0:
            return f'{food_item.item_name} has expired! Please check and dispose if spoiled.'
        elif days_until_expiry is not None and days_until_expiry <= 1:
            return f'{food_item.item_name} expires today! Use immediately.'
        elif days_until_expiry is not None and days_until_expiry <= 3:
            return f'{food_item.item_name} expires in {days_until_expiry} days. Use soon!'
        elif risk_score >= 70:
            return f'{food_item.item_name} is at high risk of waste. Take action now.'
        elif risk_score >= 40:
            return f'{food_item.item_name} needs attention. Plan to use soon.'
        else:
            return f'{food_item.item_name} status update.'