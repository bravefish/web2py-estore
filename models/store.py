UNDEFINED = -1


if request.env.web2py_runtime_gae:            # if running on Google App Engine
    store = DAL('gae')                           # connect to Google BigTable
    session.connect(request, response, db=store) # and store sessions and tickets there
else:
    store = DAL("sqlite://store.db")


store.define_table('category', 
    Field('name'), 
    Field('description', 'text'),
    Field('small_image', 'upload'),
)


store.define_table('product', 
    Field('name'),
    Field('category', store.category),
    Field('description', 'text', default=''),
    Field('small_image', 'upload'),
    Field('large_image', 'upload', default=''),
    Field('quantity_in_stock', 'integer', default=UNDEFINED), # if UNDEFINED, don't show
    Field('max_quantity', 'integer', default=0), # maximum quantity that can be purchased in an order. If 0, no limit. If UNDEFINED, don't show.
    Field('price', 'double', default=1.0),
    Field('old_price', 'double', default=0.0),
    Field('weight_in_pounds', 'double', default=1),
    Field('tax_rate_in_your_state', 'double', default=10.0),
    Field('tax_rate_outside_your_state', 'double', default=0.0),
    Field('featured', 'boolean', default=False),
    Field('allow_rating', 'boolean', default=False),
    Field('rating', 'integer', default='0'),
    Field('viewed', 'integer', default='0'),
    Field('clicked', 'integer', default='0'))


# each product can have optional addons
store.define_table('option',
    Field('product', store.product),
    Field('description'),
    Field('price', 'double', default=1.0),
)


# support for merchandising
# for p1 show p2, and for p2 show p1
store.define_table('cross_sell',
    Field('p1', store.product),
    Field('p2', store.product),
)
# for product, show better, but not the reverse
store.define_table('up_sell',
    Field('product', store.product),
    Field('better', store.product),
)


store.define_table('comment', 
    Field('product', store.product), 
    Field('author'), 
    Field('email'), 
    Field('body', 'text'), 
    Field('rate', 'integer')
)


store.define_table('info', 
    Field('google_merchant_id', default='[google checkout id]', length=256),
    Field('name', default='[store name]'),
    Field('headline', default='[store headline]'), 
    Field('address', default='[store address]'), 
    Field('city', default='[store city]'), 
    Field('state', default='[store state]'), 
    Field('zip_code', default='[store zip]'), 
    Field('phone', default='[store phone number]'), 
    Field('fax', default='[store fax number]'), 
    Field('email', requires=IS_EMAIL(), default='yourname@yourdomain.com'), 
    Field('description', 'text', default='[about your store]'), 
    Field('why_buy', 'text', default='[why buy at your store]'), 
    Field('return_policy', 'text', default='[what is your return policy]'), 

    Field('logo', 'upload', default=''), 
    Field('color_background', length=10, default='white'), 
    Field('color_foreground', length=10, default='black'), 
    Field('color_header', length=10, default='#F6F6F6'), 
    Field('color_link', length=10, default='#385ea2'), 
    Field('font_family', length=32, default='arial,  helvetica'), 

    Field('ship_usps_express_mail', 'boolean', default=True), 
    Field('ship_usps_express_mail_fc', 'double', default=0), 
    Field('ship_usps_express_mail_vc', 'double', default=0), 
    Field('ship_usps_express_mail_bc', 'double', default=0), 
    Field('ship_usps_priority_mail', 'boolean', default=True), 
    Field('ship_usps_priority_mail_fc', 'double', default=0), 
    Field('ship_usps_priority_mail_vc', 'double', default=0), 
    Field('ship_usps_priority_mail_bc', 'double', default=0), 
    Field('ship_ups_next_day_air', 'boolean', default=True), 
    Field('ship_ups_next_day_air_fc', 'double', default=0), 
    Field('ship_ups_next_day_air_vc', 'double', default=0), 
    Field('ship_ups_next_day_air_bc', 'double', default=0), 
    Field('ship_ups_second_day_air', 'boolean', default=True), 
    Field('ship_ups_second_day_air_fc', 'double', default=0), 
    Field('ship_ups_second_day_air_vc', 'double', default=0), 
    Field('ship_ups_second_day_air_bc', 'double', default=0), 
    Field('ship_ups_ground', 'boolean', default=True), 
    Field('ship_ups_ground_fc', 'double', default=0), 
    Field('ship_ups_ground_vc', 'double', default=0), 
    Field('ship_ups_ground_bc', 'double', default=0), 
    Field('ship_fedex_priority_overnight', 'boolean', default=True), 
    Field('ship_fedex_priority_overnight_fc', 'double', default=0), 
    Field('ship_fedex_priority_overnight_vc', 'double', default=0), 
    Field('ship_fedex_priority_overnight_bc', 'double', default=0), 
    Field('ship_fedex_second_day', 'boolean', default=True), 
    Field('ship_fedex_second_day_fc', 'double', default=0), 
    Field('ship_fedex_second_day_vc', 'double', default=0), 
    Field('ship_fedex_second_day_bc', 'double', default=0), 
    Field('ship_fedex_ground', 'boolean', default=True), 
    Field('ship_fedex_ground_fc', 'double', default=0), 
    Field('ship_fedex_ground_vc', 'double', default=0), 
    Field('ship_fedex_ground_bc', 'double', default=0)
)




store.category.name.requires = IS_NOT_IN_DB(store, 'category.name')
store.product.name.requires = IS_NOT_IN_DB(store, 'product.name')
store.product.category.requires = IS_IN_DB(store, 'category.id', 'category.name')
store.product.name.requires = IS_NOT_EMPTY()
store.product.description.requires = IS_NOT_EMPTY()
store.product.quantity_in_stock.requires = IS_INT_IN_RANGE(0, 1000)
store.product.price.requires = IS_FLOAT_IN_RANGE(0, 10000)
store.product.rating.requires = IS_INT_IN_RANGE(-10000, 10000)
store.product.viewed.requires = IS_INT_IN_RANGE(0, 1000000)
store.product.clicked.requires = IS_INT_IN_RANGE(0, 1000000)
store.option.product.requires = IS_IN_DB(store, 'product.id', 'product.name')
store.cross_sell.p1.requires = IS_IN_DB(store, 'product.id', 'product.name')
store.cross_sell.p2.requires = IS_IN_DB(store, 'product.id', 'product.name')
store.up_sell.product.requires = IS_IN_DB(store, 'product.id', 'product.name')
store.up_sell.better.requires = IS_IN_DB(store, 'product.id', 'product.name')
store.comment.product.requires = IS_IN_DB(store, 'product.id', 'product.name')
store.comment.author.requires = IS_NOT_EMPTY()
store.comment.email.requires = IS_EMAIL()
store.comment.body.requires = IS_NOT_EMPTY()
store.comment.rate.requires = IS_IN_SET(range(5, 0, -1))
for field in store.info.fields:
    if field[:-2] in ['fc',  'vc']:
        store.info[field].requires = IS_FLOAT_IN_RANGE(0, 100)
        
        
if len(store(store.info.id > 0).select()) == 0:
    store.info.insert(name='[store name]')
mystore = store(store.info.id > 0).select()[0]