# Atlas des besoins d'interopérabilité des agents IA

**Édition du 1 novembre 2026 · Recherche documentaire, scénarios et plans d'évaluation non exécutés.**

Cet atlas examine vingt familles de besoins, depuis les transports et l'identité jusqu'aux effets incertains, à la mémoire, à la robotique et à la supervision d'une autonomie accrue. Il utilise les protocoles Internet comme leçons de séparation des responsabilités et confronte chaque piste aux mécanismes existants.

Chaque fiche contient un cas concret, une composition de référence, une opportunité résiduelle, un petit livrable possible, un contre-exemple, une décision et des sources primaires. Les horizons AGI/ASI sont conditionnels, sans calendrier ni capacité de certification présumée. La nécessité universelle d'un protocole futur ne peut être établie par cette carte.

## English overview

This research atlas examines twenty agent-interoperability needs and classifies each residual problem as reuse, profiling, open research, or primarily outside protocol scope. It compares proposed contributions with strong combinations of existing mechanisms. Each entry includes a concrete failure, a falsifiable evaluation plan and conditional autonomy/AGI/ASI horizons. Evaluation plans have not been executed in this publication. No production adoption, universal novelty, or safety certification is asserted.

## Parcourir le travail

- [Matrice des vingt familles](MATRICE.md)
- [Décisions transversales et inconnues](DECISIONS_ET_LIMITES.md)
- [Sources primaires](SOURCES.md)
- [Méthode, assistance IA et portée des conclusions](METHODS.md)
- [Licence CC BY 4.0](LICENSE.md)
- [Citer cette édition](CITATION.md)
- [Proposer un cas d'intégration ou un contre-exemple](CONTRIBUTING.md)

## Vingt fiches, vingt consignes

| Famille | Décision | Livrable candidat |
|---|---|---|
| [01. Réseau et transport](families/01.md) | REUTILISER | Une recette de déploiement indiquant les garanties de chaque couche et les obligations laissées au fournisseur d'effets. |
| [02. Messages et outils](families/02.md) | REUTILISER | Une fiche de mapping d'une opération concrète et de ses refus, conservant les comportements sans extension. |
| [03. Découverte et versions](families/03.md) | PROFILER | Un profil narratif de compatibilité précisant cache, changements incompatibles et refus des exigences essentielles non reconnues. |
| [04. Identité des acteurs](families/04.md) | REUTILISER | Une table d'identités, d'émetteurs acceptés, de responsabilités déclarées et de preuves nécessaires, sans annuaire universel. |
| [05. Délégation atténuée](families/05.md) | PROFILER | Une correspondance de contraintes entre deux services, avec exemples de conservation et de refus d'élargissement. |
| [06. Acceptation et consentement](families/06.md) | PROFILER | Une grille de portée du consentement et de décision d'acceptation, réutilisant les formats existants. |
| [07. Engagement sur l’action](families/07.md) | PROFILER | Un contrat narratif d'équivalence pour une action précise, avec exemples ambigus et règle de refus. |
| [08. Cycle des tâches](families/08.md) | PROFILER | Une matrice reliant états A2A, étapes du workflow et observations de l'effet pour un service concret. |
| [09. Reprise et idempotence](families/09.md) | REUTILISER | Une synthèse narrative des contrats fournisseur et des conclusions permises après réponse perdue, sans schéma ou corpus exécutable. |
| [10. Compensation](families/10.md) | PROFILER | Une fiche par effet décrivant réversibilité, compensation disponible, responsable et observation permettant d'en constater le résultat. |
| [11. Révocation](families/11.md) | PROFILER | Une matrice de décisions pour nouvelle admission, opération engagée et consultation historique, sans mécanisme de succession de clés. |
| [12. Quotas et budgets](families/12.md) | REUTILISER | Une fiche narrative des invariants d'allocation et de rapprochement, comparée à un registre transactionnel conventionnel complet. |
| [13. Reçus et provenance](families/13.md) | PROFILER | Une taxonomie narrative des affirmations, avec graphe de dépendances et limites explicites de vérification. |
| [14. Données hostiles](families/14.md) | RECHERCHE | Un modèle de menace et une classification des transitions où une donnée peut influencer cible, paramètres ou sélection d'outil. |
| [15. Mémoire et confidentialité](families/15.md) | RECHERCHE | Un inventaire conceptuel des dérivés de mémoire et des points où leurs restrictions doivent être conservées. |
| [16. Attestation technique](families/16.md) | PROFILER | Un profil de claims et d'hypothèses reliant plateforme, médiation et opération, sans inventer une attestation fournisseur. |
| [17. Robotique et monde physique](families/17.md) | HORS_PROTOCOLE | Une frontière d'intégration documentant commande acceptée, commande encore applicable et arrêt effectivement constaté, sous hypothèses mécaniques explicites. |
| [18. Paiements et responsabilité](families/18.md) | HORS_PROTOCOLE | Une grille narrative séparant autorisation, initiation, règlement, prestation, contestation et compensation, avec l'acteur capable d'attester chaque fait. |
| [19. Conformité et gouvernance](families/19.md) | PROFILER | Un guide de lecture des preuves et de gouvernance des extensions, avec règles de non-transfert des résultats entre versions. |
| [20. Supervision d’une autonomie supérieure](families/20.md) | RECHERCHE | Une carte de garanties conditionnelles : propriété, modèle, composant de contrôle, hypothèses et événement qui rend la garantie inapplicable. |

## Attribution

Direction de recherche : **Mohammed Messaoudene**. Synthèse, rédaction et contre-lectures assistées par IA, notamment ChatGPT Pro et Codex. Ces lectures ne constituent pas une expertise humaine ou institutionnelle indépendante. Aucun lien avec DARPA ni caution d'un organisme de normalisation n'est revendiqué.

Cette nouvelle étude narrative dispose de sa propre portée de licence. Elle ne modifie pas les versions, licences, résultats ou identifiants des autres travaux hébergés dans le dépôt. Les résultats expérimentaux historiques d'AIGP ne sont pas des expériences exécutées pour cet atlas.
