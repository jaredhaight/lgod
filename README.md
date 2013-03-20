Live Geek or Die 
================
Live Geek or Die (http://www.livegeekordie.com) is a news and opinion site about technology. I designed the backend and the layout and responsive design of the frontend.
The stack consits of Varnish, Nginx, Django and MySQL. It is the second site that I have built.

Stuff I did on the front end that I think is cool
-------------------------------------------------

* Responsive design using Bootstrap and Response.js to swap in photos sized appropriately for the viewport.
* Notes slider on the home page will switch between 4 notes on 3 cards to 2 notes on 6 cards depending on viewport. The slider is handled by royalslider.js.
* Article Editor with autosaving.

Stuff I did on the back end that I think is cool
------------------------------------------------

* The crop for Article images is handled with jCrop. When a crop is selected, thumbnails are automatically generated and uploaded to CloudFiles
* There are three types of articles, and the WYSIWYG editor checks to make sure that the article is valid for it's type before allowing it to be posted (this is done with javascript on the frontend and then through python on the backend)
* Roles are instituted for editors and regular staff
* A cron job pulls in Google Analytics Pageviews, Twitter Shares and Facebook likes every 15 minutes. This is displayed on a staff dashboard
* Data from the MySQL DB from the old Drupal site was imported into the new site.
* Links from the old site redirect to the appropriate article.
