FROM nginx

# Replacing nging configuration with custome one
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx

EXPOSE 80/tcp
EXPOSE 443/tcp
