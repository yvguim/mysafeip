# MySafeIp

## MySafeIp is a web app acting as a trusted IP source for firewalls.
With it, I don't have to open my own services (Nextcloud, bitwarden, etc...) worldwilde. Just me, my family and friends can use those services easily. Family and friends don't even need an account to mysafeip with instant link feature.
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
