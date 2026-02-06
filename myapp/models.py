from django.db import models

class Register(models.Model):
    kh_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, null=True, blank=True)
    password = models.CharField(max_length=100)
    rights = models.CharField(max_length=100, default='user')
    is_active = models.BooleanField(default=True)   # REQUIRED FOR BLOCK

    def __str__(self):
        return self.name

class Menu(models.Model):
    itemname = models.CharField(max_length=100)
    category = models.CharField(max_length=100,null=True)
    itemimage = models.ImageField(upload_to='menu/')
    itemprice = models.IntegerField()
    special = models.CharField(max_length=100,null=True)
    def __str__(self):
        return self.itemname

class Cart(models.Model):
    table=models.IntegerField()
    item=models.ForeignKey(Menu,on_delete=models.CASCADE)
    quantity=models.IntegerField()
    status=models.CharField(max_length=100,default='Pending')
    def __str__(self):
        return f'{self.table}'


class Order(models.Model):
    table = models.IntegerField()
    item = models.ForeignKey('Menu', on_delete=models.CASCADE, null=True, blank=True)
    combo = models.ForeignKey('ComboOffer', on_delete=models.CASCADE, null=True, blank=True)
    special_offer = models.ForeignKey('SpecialOffer', on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.IntegerField(default=1)
    status = models.CharField(max_length=20, default='Pending')
    date = models.DateTimeField(auto_now_add=True,null=True)

    def get_price(self):
        if self.item:
            return self.item.itemprice
        elif self.combo:
            return self.combo.combo_price
        elif self.special_offer:
            return self.special_offer.offer_price
        return Decimal('0.00')

    def get_total_price(self):
        return self.get_price() * self.quantity

    def get_item_name(self):
        if self.item:
            return self.item.itemname
        elif self.combo:
            return self.combo.combo_name
        elif self.special_offer:
            return self.special_offer.offer_name
        return "Unknown Item"

class Sale(models.Model):
    table=models.IntegerField()
    item=models.ForeignKey(Menu,on_delete=models.CASCADE)
    quantity=models.IntegerField()
    amount=models.IntegerField()
    def __str__(self):
        return f'{self.table}'

class Combo(models.Model):
    # ... other fields ...

    # Change the field definition to allow NULL and BLANK
    menuid = models.ForeignKey(
        'Menu',
        on_delete=models.CASCADE,
        null=True,  # <-- Crucial change: allows NULL in the database
        blank=True  # <-- Recommended: allows it to be blank in forms
    )


# In your models.py file

class SpecialOffer(models.Model):
    offer_name = models.CharField(max_length=255, unique=True)
    items = models.ForeignKey(Menu, related_name='special_offers',on_delete=models.CASCADE,null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # ADD THIS FIELD: Use DecimalField for accurate currency storage
    offer_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return self.offer_name

class ComboOffer(models.Model):
    """
    Model to store Combo offers (requires minimum 2 items).
    """
    combo_name = models.CharField(max_length=255, unique=True)
    # Links to Menu items
    items = models.ManyToManyField('Menu', related_name='combo_offers')
    # Use DecimalField for accurate currency storage
    combo_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    image=models.ImageField(upload_to='img/',null=True)
    def __str__(self):
        return self.combo_name

class SpecialOfferCart(models.Model):
    table=models.IntegerField()
    item=models.ForeignKey(SpecialOffer,on_delete=models.CASCADE,null=True)
    quantity=models.IntegerField()
    status=models.CharField(max_length=100,default='Pending')
    def __str__(self):
        return f'{self.table}'

class ComboOfferCart(models.Model):
    table=models.IntegerField()
    item=models.ForeignKey(ComboOffer,on_delete=models.CASCADE,null=True)
    quantity=models.IntegerField()
    status=models.CharField(max_length=100,default='Pending')
    def __str__(self):
        return f'{self.table}'