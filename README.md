
# Tissegram

## Webhook install with Nginx and letsencrypt

Install Cerbot and edit its conf :

    apt install certbot
    apt install python-certbot-nginx
    nano /etc/nginx/sites-available/webhook

Inside my /etc/nginx/sites-available/webhook :

    server {
	    listen 80;
	    server_name webhook.yourdomain.com;
	    
	    location /<TOKEN>{
		    proxy_pass http://127.0.0.1:5001;
		    include /etc/nginx/proxy_params;
		}
	}

Now, let's enable conf and run Cerbot :

    ln -s /etc/nginx/sites-available/webhook /etc/nginx/sites-enabled/webhook
    systemctl reload nginx.service
    certbot --nginx
    nano /etc/nginx/sites-available/webhook

Modify /etc/nginx/sites-available/webhook :

    server {
	    listen 443 ssl;
	    server_name webhook.yourdomain.com;
	    
	    ssl on;
	    ssl_certificate /etc/letsencrypt/live/webhook.yourdomain.com/fullchain.pem;
	    ssl_certificate_key /etc/letsencrypt/live/webhook.yourdomain.com/privkey.pem;
	    include /etc/letsencrypt/options-ssl-nginx.conf;
	    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
	    
	    location /<TOKEN>{
		    proxy_pass http://127.0.0.1:5001;
		    include /etc/nginx/proxy_params;
		}
	}

 And reload Nginx :

    systemctl reload nginx.service

## Tissegram install

Install dependency :

    pip install .

Run main script :

    python tissegram.py -c myconf.ini
