from pprint import pprint
import pytz
import gocardless
import braintree
# import gocardless_pro
import paypalrestsdk as paypal

from website.config import settings
from website.config.settings import app_domain

from website.config.logger import log

PROVIDER_ID = {'gocardless':1, 'paypal': 2}
PROVIDER_NAME = {1: 'gocardless', 2: 'paypal'}

payment_providers = {
    'paypal': {              
        "mode": "sandbox", # sandbox or live
        'credentials': {
            "mode": "sandbox", # sandbox or live
            "client_id": "AaGlNEvd26FiEJiJi53nfpXh19_oKetteV1NGkBi4DDYZSqBexKVgaz9Lp0SI82gYFSAYpsmxO4iDtxU",
            "client_secret": "EMcIuDJE_VDNSNZS7C7NLi9DEHaDvVu9jlIYyCCHaLmrLuy_VQ6C0bbcRnyF-7B6CcN__Dn6HqUwsgMG"}
        },
    'gocardless':{
        'environment': 'sandbox',
        'credentials': {
            'app_id': 'MNHBS3C4X4ZG211SM70WSS7WCN8B3X1KAWZBKV9S8N6KH2RNH6YZ5Z5865RFD3H6',
            'app_secret': 'NE4NWYDQY4FNN1B47VT9SZ318GPQND130DW7QGQ73JMVTZQZHJQNF23ZFNP48GKV',
            'access_token': 'CJ7G7V36VAH5KVAHTYXD8VE8M4M0S41EQXH2E1HTGV5AN5TAZBER36ERAF4CG2NR',
            'merchant_id': '11QFXD7TTA',
        },
        'redirect_url':'https://test.maidstone-hackspace.org.uk'
    }
}


def select_provider(type):
    if type == "gocardless": return gocardless_provider()
    if type == "braintree": return braintree_provider()
    if type == "paypal": return paypal_provider()

    log.exception('[scaffold] - "No Provider for ' + type)
    assert 0, "No Provider for " + type

class gocardless_provider:
    form_remote = True
    client = None

    def __init__(self):
        # gocardless are changing there api, not sure if we can switch yet
        # self.client = gocardless_pro.Client(
        #     access_token=settings.payment_providers['gocardless']['credentials']['access_token'],
        #     environment=settings.payment_providers['gocardless']['environment'])

        print(settings.payment_providers.keys)
        gocardless.environment = settings.payment_providers['gocardless']['environment']
        gocardless.set_details(**settings.payment_providers['gocardless']['credentials'])
        self.client = gocardless.client.merchant()

    def subscribe_confirm(self, args):
        response = gocardless.client.confirm_resource(args)
        subscription = gocardless.client.subscription(args.get('resource_id'))
        return {
            'amount': subscription.amount,
            'start_date': subscription.created_at,
            'reference': subscription.id
        }

    def fetch_subscriptions(self):
        for paying_member in self.client.subscriptions():
            user=paying_member.user()
            # for bill in paying_member.bills():
            #     print('test')
            #     print(dir(bill))
            #     print(bill.created_at)
            print(dir(paying_member))
            print(paying_member.reference_fields)
            yield {
                'status': paying_member.status,
                'email': user.email,
                'start_date': paying_member.created_at,
                'reference': paying_member.id,
                'amount': paying_member.amount}

    def get_redirect_url(self):
        return settings.payment_providers['gocardless']['redirect_url']

    def get_token(self):
        return 'N/A'

    def create_subscription(self, amount, name, redirect_success, redirect_failure, interval_unit='month', interval_length='1'):
        return gocardless.client.new_subscription_url(
            amount=float(amount), 
            interval_length=interval_length, 
            interval_unit=interval_unit,
            name=name,
            redirect_uri=redirect_success)


class braintree_provider:
    form_remote = False

    def __init__(self):
        braintree.Configuration.configure(
            environment=braintree.Environment.Sandbox,
            merchant_id=settings.payment_providers['braintree']['credentials']['merchant_id'],
            public_key=settings.payment_providers['braintree']['credentials']['public_key'],
            private_key=settings.payment_providers['braintree']['credentials']['private_key'])

    def get_token(self):
        return braintree.ClientToken.generate()


    def create_subscription(self, amount, name, redirect_success, redirect_failure, interval_unit='month', interval_length='1'):
        result = braintree.Customer.create({
            "first_name": "test",
            "last_name": "user",
            "payment_method_nonce": nonce_from_the_client
        })

        return braintree.Subscription.create({
            "payment_method_token": "the_token",
            "plan_id": "membership",
            "merchant_account_id": "gbp_sandbox"
            #"price": "20.00"
            #'name': name
        })

    def fetch_subscriptions(self):
        for paying_member in braintree.Subscription.search(braintree.SubscriptionSearch.status == braintree.Subscription.Status.Active):
            user=paying_member.user()
            yield {
                'status': paying_member.status,
                'email': user.email,
                'start_date': paying_member.created_at,
                'reference': paying_member.reference,
                'amount': paying_member.amount}


class payment:
    """
    paypal reference = https://github.com/paypal/PayPal-Python-SDK
    gocardless reference = https://github.com/paypal/PayPal-Python-SDK
    """
    #~ def __call__(self, **args):
        #~ return self

    def __init__(self, provider='gocardless', style='payment', mode='sandbox'):
        self.provider = provider
        self.environment = int(mode=='production')
        self.provider_id = PROVIDER_ID.get(provider)

        print(settings.payment_providers)
        if provider == 'paypal':
            paypal.configure(**settings.payment_providers[provider]['credentials'])
            return

        gocardless_pro.Client(
            access_token=settings.payment_providers[provider]['credentials']['access_token'],
            environment=settings.payment_providers[provider])
        #~ environment = int('production' = settings.payment_providers[provider]['environment'])
        gocardless.environment = settings.payment_providers[provider]['environment']
        gocardless.set_details(**settings.payment_providers[provider]['credentials'])
        merchant = gocardless.client.merchant()

    def lookup_provider_by_id(self, provider_id):
        return PROVIDER_NAME.get(provider_id, None)

    def make_donation(self, amount, reference, redirect_success, redirect_failure):
        if self.provider == 'paypal':
            payment = paypal.Payment({
                "intent": "sale",
                "payer": {"payment_method": "paypal"},
                "redirect_urls": {
                    "return_url": redirect_success,
                    "cancel_url": redirect_failure},

                "transactions": [{
                    "amount": {
                        "total": amount,
                        "currency": "GBP"},
                    "description": reference}]})

            payment_response = payment.create()
            print('payment create')
            if payment_response:
                print(payment_response)
                for link in payment.links:
                    if link.method == "REDIRECT":
                        redirect_url = str(link.href)
                        print(redirect_url)
                        return str(redirect_url)
            else:
                print("Error while creating payment:")
                print(payment.error)

        if self.provider == 'gocardless':
            return gocardless.client.new_bill_url(
                float(amount),
                name=reference,
                redirect_uri=redirect_success)

        return 'Error something went wrong'

    def fetch_subscriptions(self):
        if self.provider == 'gocardless':
            merchant = gocardless.client.merchant()
            for paying_member in merchant.subscriptions():
                user=paying_member.user()
                print(dir(paying_member)) 
                print(paying_member.next_interval_start) 
                print(paying_member.status) 
                print(dir(paying_member.user())) 
                yield {
                    'email': user.email,
                    'start_date': paying_member.created_at,
                    'reference': paying_member.id,
                    'amount': paying_member.amount}

        if self.provider == 'paypal':
            #~ I-S39170DK26AF
            #~ start_date, end_date = "2014-07-01", "2014-07-20"
            billing_agreement = paypal.BillingAgreement.find('')
            print(billing_agreement)
            print(dir(billing_agreement))
            #~ print billing_agreement.search_transactions(start_date, end_date)
            #~ transactions = billing_agreement.search_transactions(start_date, end_date)
            payment_history = paypal.Payment.all({"count": 2})

            # List Payments
            print("List Payment:")
            print(payment_history)
            for payment in payment_history.payments:
                print("  -> Payment[%s]" % (payment.id))
            #~ print paypal.BillingAgreement.all()
            history = paypal.BillingPlan.all(
                {"status": "CREATED", "page_size": 5, "page": 1, "total_required": "yes"})
            print(history)

            print("List BillingPlan:")
            for plan in history.plans:
                print(dir(plan))
                print(plan.to_dict())
                print("  -> BillingPlan[%s]" % (plan.id))
    
            #~ merchant = gocardless.client.merchant()
            #~ for paying_member in merchant.subscriptions():
                #~ user=paying_member.user()
                #~ yield {
                    #~ 'email': user.email,
                    #~ 'start_date': paying_member.created_at,
                    #~ 'reference': paying_member.id,
                    #~ 'amount': paying_member.amount}

    def subscribe_confirm(self, args):
        if self.provider == 'gocardless':
            response = gocardless.client.confirm_resource(args)
            subscription = gocardless.client.subscription(args.get('resource_id'))
            return {
                'amount': subscription.amount,
                'start_date': subscription.created_at,
                'reference': subscription.id
            }

        if self.provider == 'paypal':
            print('subscribe_confirm')
            payment_token = args.get('token', '')
            billing_agreement_response = paypal.BillingAgreement.execute(payment_token)
            amount = 0
            print(billing_agreement_response)
            print(billing_agreement_response.id)
            for row in billing_agreement_response.plan.payment_definitions:
                amount = row.amount.value

            return {
                'amount': amount,
                'start_date': billing_agreement_response.start_date,
                'reference': billing_agreement_response.id
            }

        return None

    def unsubscribe(self, reference):
        if self.provider == 'gocardless':
            print('unsubscribe gocardless')
            subscription = gocardless.client.subscription(reference)
            print(subscription.cancel())

        if self.provider == 'paypal':
            # this may be wrong
            # ManageRecurringPaymentsProfileStatus 
            print(reference)
            billing_plan = paypal.BillingAgreement.find(reference)
            print(billing_plan)
            print(billing_plan.error)
            #~ billing_plan.replace([{"op": "replace","path": "/","value": {"state":"DELETED"}}])
            print(billing_plan.error)
            #~ invoice = paypal.Invoice.find(reference)
            options = {
                "subject": "Cancelling membership",
                "note": "Canceling invoice",
                "send_to_merchant": True,
                "send_to_payer": True
            }

            if billing_plan.cancel(options):  # return True or False
                print("Invoice[%s] cancel successfully" % (invoice.id))
            else:
                print(billing_plan.error)


    def subscribe(self, amount, name, redirect_success, redirect_failure, interval_unit='month', interval_length='1'):
        if self.provider == 'gocardless':
            return gocardless.client.new_subscription_url(
                amount=float(amount), 
                interval_length=interval_length, 
                interval_unit=interval_unit,
                name=name,
                redirect_uri=redirect_success)

        if self.provider == 'paypal':
            billing_plan = paypal.BillingPlan({
                "name": name,
                "description": "Membership subscription",
                "merchant_preferences": {
                    "auto_bill_amount": "yes",
                    "cancel_url": redirect_failure,
                    "initial_fail_amount_action": "continue",
                    "max_fail_attempts": "1",
                    "return_url": redirect_success,
                    "setup_fee": {
                        "currency": "GBP",
                        "value": amount
                    }
                },
                "payment_definitions": [{
                        "amount": {
                            "currency": "GBP",
                            "value": amount
                        },
                        "cycles": "0",
                        "frequency": interval_unit,
                        "frequency_interval": interval_length,
                        "name": "Regular 1",
                        "type": "REGULAR"
                    }
                ],
                "type": "INFINITE"
            })
            print('create bill')
            
            response = billing_plan.create()
            
            billing_plan = paypal.BillingPlan.find(billing_plan.id)
            
            if billing_plan.activate():
                start_date = datetime.utcnow() + timedelta(minutes=10)
                billing_agreement = paypal.BillingAgreement({
                    "name": billing_plan.name,
                    "description": name,
                    "start_date": start_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "plan": {"id": str(billing_plan.id)},
                    "payer": {"payment_method": "paypal"}
                })
                
                if billing_agreement.create():
                    print('billing agreement id')
                    print(billing_agreement.id)
                    
                    for link in billing_agreement.links:
                        if link.rel == "approval_url":
                            approval_url = link.href
                            return approval_url
                else:
                    print(billing_agreement.error)
                    print('failed')

    def confirm(self, args):
        confirm_details = {}
        confirm_details['successfull'] = False
        print('---------------------')
        print(args)
        

        
        from pprint import pprint
        if self.provider == 'paypal':
            print(args.get('paymentId'))
            print(args.get('PayerID'))
            payment = paypal.Payment.find(args.get('paymentId'))
            pprint(payment)
            print(pprint(payment))
            print(payment)
            
            confirm_details['name'] = payment['payer']['payer_info'].first_name + ' ' + payment['payer']['payer_info'].last_name
            confirm_details['user'] = payment['payer']['payer_info'].email
            confirm_details['status'] = payment.state
            confirm_details['amount'] = payment['transactions'][0]['amount'].total
            confirm_details['created'] = payment.create_time
            confirm_details['reference'] = payment.id
            pprint(confirm_details)
            
            
            if payment.execute({"payer_id": args.get('PayerID')}):  # return True or False
                confirm_details['successfull'] = True
                print("Payment[%s] execute successfully" % (args.get('paymentId')))
            else:
                print(payment.error)
            return confirm_details

        if self.provider == 'gocardless':
            bill_id = args.get('resource_id')
            gocardless.client.confirm_resource(args)
            if bill_id:
                bill = gocardless.client.bill(bill_id)
                confirm_details['name'] = bill.name
                confirm_details['user'] = bill.user
                confirm_details['status'] = bill.status
                confirm_details['amount'] = bill.amount
                #~ confirm_details['amount_minus_fees'] = bill.amount_minus_fees
                confirm_details['created'] = bill.created_at
                confirm_details['reference'] = bill_id
                confirm_details['successfull'] = True
                return confirm_details
        return None
