# MySafeIp

For english version, [it's here!](./README.md)

## MySaFeip est une application Web agissant comme un tiers de confiance pour les pare-feu.
Avec cela, je n'ai pas à ouvrir mes propres services (NextCloud, Bitwarden, etc ...) au monde entier. Juste moi, ma famille et mes amis peuvent utiliser ces services facilement. La famille et les amis n'ont même pas besoin d'un compte grace aux liens instantanés. J'espère qu'il pourra vous rendre les mêmes services.

MySafeIP est livré avec un [Conteneur Docker] (https://github.com/yvguim/mysafeip-compose) et un [client] (https://github.com/yvguim/mysafeip-client) pour récupérer les IP de confiance.
<p align="center">
  <img width="400" height="383" src="https://raw.githubusercontent.com/yvguim/mysafeip/main/docs/diag.png">
</p>

***Astuce***: L'utilisateur n'a pas besoin de connaître son IP publique, MySafeIP vérifiera directement les en-têtes HTTP.

Il est basé sur le framework [Fastapi] (https://github.com/tiangolo/fastapi) et est disponible en anglais et en français.

Je considère MySAFEIP 0.9 comme une version alpha pour le moment (une meilleure organisation de code, de la refactorisation et des tests arrivent) mais cela fonctionne assez "out of the box".

## Vous pouvez:
- Déclarer une ou plusieurs IP de confiance;
- Déclarez un lien accessible à tout le monde: MySaFeip agit comme un redirecteur d'URL et enregistre l'IP du client à la volée;

## C'est facile à installer (docker inside):
- MySafeIP s'installe facilement avec docker: https://github.com/yvguim/mysafeip-compose
- MySafeIp-client se configure aussi facilement: https://github.com/yvguim/mysafeip-client

## Quelques copies d'écran:
### L'accueil
![](https://raw.githubusercontent.com/yvguim/mysafeip/main/docs/cap0.png)
### La déclaration d'IP
![](https://raw.githubusercontent.com/yvguim/mysafeip/main/docs/cap1.png)
### Les liens instantanés
![](https://raw.githubusercontent.com/yvguim/mysafeip/main/docs/cap2.png)

## Jetez un coup d'oeil à la demo sur Youtube:

Disponible bientôt ;)
