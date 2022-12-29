# MySafeIp

## MySafeIp is a web app acting as a trusted IP source for firewalls.
It allows registered people declare their IP manually or automatically on the app and to be allowed by their firewalls on the fly.
It comes with a [docker container](https://github.com/yvguim/mysafeip-compose) and a [client](https://github.com/yvguim/mysafeip-client) to retrieve IP from server.
<p align="center">
  <img width="400" height="383" src="https://raw.githubusercontent.com/yvguim/mysafeip/main/docs/diag.png">
</p>

***Tips***: User don't need to know his public IP, Mysafeip will check http headers directly. It also apply to instant links users.

It is built on top of [Fastapi](https://github.com/tiangolo/fastapi) framework and available in English and French.

I consider MySafeIp 0.9 as an Alpha version for the moment (better code organisation, refactoring and tests are coming) but it works pretty well out of the box.

## Users can:
- Declare one or more IP;
- Declare a link accessible to everyone: MySafeIP acts like a url redirector and registers client IP on the fly;
- Create an auth token for mysafeip-client;

## It's easy to install (docker inside):
- MySafeIP can be easily installed with docker: https://github.com/yvguim/mysafeip-compose
- MySafeIp-client can be configured easily too: https://github.com/yvguim/mysafeip-client

## Some screenshots:
### Homepage
![](https://raw.githubusercontent.com/yvguim/mysafeip/main/docs/cap0.png)
### IP declaration
![](https://raw.githubusercontent.com/yvguim/mysafeip/main/docs/cap1.png)
### Instant links
![](https://raw.githubusercontent.com/yvguim/mysafeip/main/docs/cap2.png)

## Check the demo on Youtube:

Available soon ;)
