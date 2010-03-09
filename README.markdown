# giraffe #

This is an experimental project to make an activity-ated personal web site application with Django.


## Setting up ##

To get started:

* Install the `giraffe` app.
* Make a new Django project.
* Add the `giraffe` and `django.contrib.admin` apps to your project.

Then you can create your profile.

### Creating a profile ###

In the Django admin, go to `Giraffe` → `People` → `Add`. Enter a display name and tick `Is site owner`. Save this new `Person` record.

Once you've added a `Person`, you can import your accounts. Use the `importaccounts` management command to do that:

    $ python manage.py importaccounts <your URL> 1

This will look up the URL you entered in the Google Social Graph API, adding that URL and any equivalent claimed URLs from the API as `Account` records. You can then look at the `Account` list in the admin to see all your new accounts.

Once you have accounts, you can poll for activity.

### Polling for activity ###

Run the `runurlpoller` management command to poll your accounts for activity:

    $ python manage.py runurlpoller

This will fetch all the activity streams from your known accounts, recording the activities found therein and their related content objects. Once that's done, check out all the new records in the `Activities` table in the admin!


## Yays ##

That's about all it does right now. Hopefully it will improve in the future.
