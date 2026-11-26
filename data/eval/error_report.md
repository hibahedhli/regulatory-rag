# Rapport d'erreurs : mode `hybrid`, k = 5

Questions : 32 (évaluation automatique) et 22 (test manuel dans l'interface) · cas à analyser : 11 (dont 7 erreurs réelles, 1 limite et 3 succès fragiles)

| Type | Nombre |
|---|---|
| Question sans réponse acceptée à tort | 2 |
| Faux refus (réponse présente refusée) | 2 |
| Réponse incohérente | 1 |
| Citations sans rapport avec la réponse | 1 |
| Erreur d'extraction (encodage) | 1 |
| Limite d'exhaustivité | 1 |
| Succès fragile (à surveiller) | 3 |

(... cas 1 à 5 inchangés ...)

## Cas 1 : Question sans réponse acceptée à tort

**Question :** Quelle est l'amende en cas de non-respect du télétravail ?
**Attendu :** aucune réponse dans le corpus (proche du corpus (télétravail, amende) mais aucun article ne prévoit cette sanction)
**Pertinence estimée :** similarité = 0.8686, recouvrement = 0.8, jugée présente
**Par mode :** hybrid: acceptée · dense: acceptée · bm25: acceptée

**Passages retrouvés :**

1. `loi-demo-protection-donnees` · Article 11 (score 0.0323) : Le non-respect des obligations de notification prévues à l'article 8 est puni d'une amende pouvant atteindre 50 000 dinars. Le traitement sans consentement valable est puni d'une amende pouvant atteindre 100 000 dinars.
2. `reglement-demo-hygiene` · Article 6 (score 0.0318) : Le non-respect de la chaîne du froid est puni d'une amende pouvant atteindre 5 000 dinars, et de la fermeture temporaire de l'établissement en cas de récidive.
3. `arrete-demo-teletravail` · Article 6 (score 0.0310) : Un accident survenu sur le lieu où est exercé le télétravail pendant les horaires de travail est présumé être un accident du travail.

**Cause probable (automatique) :** Question proche du corpus : les mots et le sens correspondent à des articles existants, donc les signaux de pertinence ne peuvent pas détecter l'absence. Seul le LLM (prompt) peut refuser dans ce cas.

**Analyse :** _La question porte sur un sujet présent dans le corpus (télétravail, amende), mais aucun article ne prévoit de sanction. La recherche ramène les articles 11 (loi) et 6 (hygiène), qui partagent seulement les mots « non-respect » et « amende ». Les trois modes acceptent la question. Le score de similarité (0,8686) est proche de celui d'une bonne réponse (0,8774 pour les sauvegardes) : aucun seuil ne sépare les deux cas. Amélioration : une étape de vérification par le LLM (« l'extrait répond-il à la question ? ») ou un reranker, en plus de la consigne de refus du prompt._

## Cas 2 : Question sans réponse acceptée à tort

**Question :** Quel est le délai de recours contre un refus d'accès aux données personnelles ?
**Attendu :** aucune réponse dans le corpus (proche du corpus (recours, données personnelles) mais le recours de 10 jours concerne les marchés publics)
**Pertinence estimée :** similarité = 0.8865, recouvrement = 0.571, jugée présente
**Par mode :** hybrid: acceptée · dense: acceptée · bm25: acceptée

**Passages retrouvés :**

1. `loi-demo-protection-donnees` · Article 5 (score 0.0328) : Toute personne a le droit d'accéder à ses données personnelles. Le responsable du traitement répond à la demande d'accès dans un délai maximal de 30 jours à compter de sa réception. Ce délai peut être prolongé de 30…
2. `loi-demo-protection-donnees` · Article 6 (score 0.0313) : La personne concernée peut demander l'effacement de ses données lorsqu'elles ne sont plus nécessaires aux finalités pour lesquelles elles ont été collectées ou lorsqu'elle retire son consentement.
3. `loi-demo-protection-donnees` · Article 8 (score 0.0311) : En cas de violation de données personnelles présentant un risque pour les personnes, le responsable du traitement notifie l'autorité de protection des données dans un délai de 72 heures après en avoir pris connaissance.

**Cause probable (automatique) :** Question proche du corpus : les mots et le sens correspondent à des articles existants, donc les signaux de pertinence ne peuvent pas détecter l'absence. Seul le LLM (prompt) peut refuser dans ce cas.

**Analyse :** _Le droit d'accès existe (art. 5), mais le recours de 10 jours concerne les marchés publics (circulaire, art. 6). L'article 5 contient un délai de 30 jours pour répondre à une demande d'accès : le modèle pourrait le confondre avec un délai de recours. La similarité (0,8865) dépasse celle de deux bonnes réponses (0,8774 et 0,8781). Amélioration : même vérification, et un prompt qui exige que l'extrait traite précisément de la notion demandée (recours)._

## Cas 3 : Succès fragile (à surveiller)

**Question :** À quelle fréquence faut-il tester la restauration des sauvegardes ?
**Attendu :** decret-demo-securite-si · Article 4 → rang 1
**Pertinence estimée :** similarité = 0.8774, recouvrement = 0.4, jugée présente
**Par mode :** hybrid: 1 · dense: 1 · bm25: 1

**Passages retrouvés :**

1. `decret-demo-securite-si` · Article 4 (score 0.0328) : Les données critiques font l'objet de sauvegardes quotidiennes. Une copie des sauvegardes est conservée hors site, et un test de restauration est réalisé au moins une fois par semestre.
2. `loi-demo-protection-donnees` · Article 9 (score 0.0161) : Les données personnelles ne sont pas conservées au-delà de la durée nécessaire aux finalités du traitement. À défaut de durée spécifique fixée par un texte, la durée de conservation ne peut excéder 5 ans après la fin de…
3. `charte-demo-donnees-ouvertes` · Article 4 (score 0.0159) : Les administrations conservent les archives de leurs jeux de données pendant 10 ans après leur dernière mise à jour.

**Cause probable (automatique) :** Bon passage en 1re position, mais avec une faible marge ou un faible recouvrement lexical.

**Analyse :** _Le bon passage est au rang 1 avec une grande marge. Le recouvrement lexical est faible (0,4) : la question dit « fréquence » et « tester la restauration », le texte dit « au moins une fois par semestre ». Seule la proximité sémantique fait gagner, et un BM25 seul échouerait avec une formulation plus éloignée. Amélioration : garder la recherche hybride, ajouter une réécriture de la requête._

## Cas 4 : Succès fragile (à surveiller)

**Question :** Sous combien de temps notifier une violation de données à l'autorité ?
**Attendu :** loi-demo-protection-donnees · Article 8 → rang 1
**Pertinence estimée :** similarité = 0.9059, recouvrement = 0.429, jugée présente
**Par mode :** hybrid: 1 · dense: 1 · bm25: 1

**Passages retrouvés :**

1. `loi-demo-protection-donnees` · Article 8 (score 0.0328) : En cas de violation de données personnelles présentant un risque pour les personnes, le responsable du traitement notifie l'autorité de protection des données dans un délai de 72 heures après en avoir pris connaissance.
2. `reglement-demo-hygiene` · Article 4 (score 0.0291) : Tout incident sanitaire grave est déclaré à l'autorité de contrôle dans un délai de 48 heures à compter de sa constatation.
3. `loi-demo-protection-donnees` · Article 7 (score 0.0290) : Tout organisme traitant les données personnelles de plus de 5 000 personnes ou traitant des données sensibles à grande échelle désigne un délégué à la protection des données (DPO).

**Cause probable (automatique) :** Bon passage en 1re position, mais avec une faible marge ou un faible recouvrement lexical.

**Analyse :** _Rang 1 correct, mais marge faible (0,0328 contre 0,0291). Le deuxième passage est le délai de 48 heures du règlement d'hygiène, un autre délai de déclaration à une autorité. Risque de confusion entre 72 et 48 heures. Amélioration : reranker, ou citer le titre du texte dans la réponse._

## Cas 5 : Succès fragile (à surveiller)

**Question :** Quel délai minimum pour remettre une offre ?
**Attendu :** circulaire-demo-marches-publics · Article 3 → rang 1
**Pertinence estimée :** similarité = 0.8781, recouvrement = 0.5, jugée présente
**Par mode :** hybrid: 1 · dense: 1 · bm25: 1

**Passages retrouvés :**

1. `circulaire-demo-marches-publics` · Article 3, p. 1 (score 0.0328) : Le délai de remise des offres ne peut être inférieur à 21 jours à compter de la publication de l'avis d'appel d'offres.
2. `circulaire-demo-marches-publics` · Article 6, p. 2 (score 0.0323) : Un candidat évincé peut former un recours devant la commission des marchés dans un délai de 10 jours à compter de la notification du rejet de son offre.
3. `charte-demo-donnees-ouvertes` · Article 3 (score 0.0308) : Toute demande de réutilisation d'un jeu de données reçoit une réponse dans un délai de 30 jours à compter de sa réception.

**Cause probable (automatique) :** Bon passage en 1re position, mais avec une faible marge ou un faible recouvrement lexical.

**Analyse :** _Marge quasi nulle (0,0328 contre 0,0323). Le deuxième passage est le recours de 10 jours, dans la même circulaire, et le mot « délai » correspond à plusieurs articles. Amélioration : reranker, ou question plus précise._


## Cas 6 : Faux refus sur un raisonnement de seuil

**Question :** Un marché de 30 000 dinars nécessite-t-il une mise en concurrence publique ?
**Attendu :** non ; en dessous de 50 000 dinars, une consultation simplifiée d'au moins trois fournisseurs suffit (circulaire, article 2)
**Réponse obtenue :** « Je n'ai pas trouvé cette information dans les textes fournis. »
**Étape fautive :** génération (LLM)

**Passage attendu :**

1. `circulaire-demo-marches-publics` · Article 2, p. 1 : Tout marché dont le montant dépasse 50 000 dinars est précédé d'une mise en concurrence publique. En dessous de ce seuil, une consultation simplifiée de trois fournisseurs au moins est suffisante.

**Cause probable :** Le montant de 30 000 dinars n'apparaît pas dans le texte. Le modèle attend une correspondance littérale au lieu de comparer le montant au seuil de 50 000 dinars. La règle de refus du prompt, formulée de façon trop stricte (les extraits doivent répondre « directement »), pousse un petit modèle comme Mistral 7B à refuser dès qu'une déduction est nécessaire.

**Analyse :** Il s'agit d'un faux refus : l'information est dans le corpus, mais elle demande une comparaison simple. Ce type de question (seuil, condition, cas particulier) est fréquent dans les textes réglementaires, donc l'erreur est gênante en pratique. Amélioration : autoriser explicitement la déduction simple dans le prompt, avec une justification en une phrase, tout en conservant le refus quand aucun extrait ne traite le sujet.

## Cas 7 : Faux refus sur une paraphrase

**Question :** Combien de temps l'État a-t-il pour payer ses fournisseurs ?
**Attendu :** 45 jours à compter de la réception de la facture (circulaire, article 5)
**Réponse obtenue :** « Je n'ai pas trouvé cette information dans les textes fournis. »
**Étape fautive :** génération (LLM), probablement

**Passage attendu :**

1. `circulaire-demo-marches-publics` · Article 5, p. 2 : L'administration règle les factures dans un délai de paiement de 45 jours à compter de leur réception. Tout retard ouvre droit à des intérêts moratoires.

**Cause probable :** Écart de vocabulaire entre la question (« l'État », « fournisseurs », « payer ») et le texte (« l'administration », « factures », « règle »). Le passage de l'article 5 est retrouvé pour d'autres questions, donc l'erreur vient probablement de la génération plutôt que de la recherche.

**Analyse :** La question ne contient presque aucun mot du texte, ce qui teste la recherche sémantique. Un modèle de 7 milliards de paramètres tolère mal ce genre d'écart et refuse par prudence. Amélioration : préciser dans le prompt que les extraits peuvent employer d'autres mots que la question. Pistes plus robustes : réécriture de la requête avant la recherche, recherche hybride, modèle plus performant.

## Cas 8 : Réponse incohérente sur une généralisation

**Question :** Le décret impose-t-il l'authentification multifacteur pour tous les systèmes ?
**Attendu :** le décret impose l'authentification multifacteur pour l'accès aux systèmes critiques (article 3) ; il ne la mentionne pas pour les autres systèmes
**Réponse obtenue :** la phrase de refus, suivie d'une explication (« Il n'est pas spécifié dans les extraits fournis que l'authentification multifacteur doit être appliquée à tous les systèmes. »), avec les citations 1 à 5
**Étape fautive :** génération (LLM) et interface

**Passage attendu :**

1. `decret-demo-securite-si` · Article 3 : L'accès aux systèmes critiques est protégé par une authentification multifacteur. Les mots de passe comportent au moins 12 caractères et sont renouvelés au minimum tous les 12 mois.

**Cause probable :** Trois défauts se cumulent : le modèle mélange la phrase de refus et une explication, contrairement à la consigne ; il cite les cinq extraits sans distinction ; et l'interface affiche « Aucune réponse dans tes documents » dès que le texte commence par la phrase de refus, alors que l'article 3 contient l'information pertinente.

**Analyse :** La réponse utile existait (la règle vise les systèmes critiques), mais l'utilisateur reçoit un message contradictoire et des sources inexploitables. Amélioration : consigne « cite uniquement les extraits que tu utilises » et « ne mélange jamais la phrase de refus avec une réponse », plus un garde-fou dans `generate_answer` qui renvoie la phrase de refus seule si la réponse commence par elle.

## Cas 9 : Limite d'exhaustivité sur une question multi-documents

**Question :** Quelles sont toutes les amendes prévues dans les textes fournis ?
**Attendu :** l'ensemble des amendes du corpus (au minimum 50 000, 100 000 et 5 000 dinars)
**Réponse obtenue :** trois amendes exactes (50 000 et 100 000 dinars de la loi, 5 000 dinars du règlement d'hygiène), suivies de « Je n'ai pas trouvé d'autres amendes dans les textes fournis. »
**Étape fautive :** recherche (nombre fixe de passages)

**Passages attendus :**

1. `loi-demo-protection-donnees` · Article 11 : Le non-respect des obligations de notification prévues à l'article 8 est puni d'une amende pouvant atteindre 50 000 dinars. Le traitement sans consentement valable est puni d'une amende pouvant atteindre 100 000 dinars.
2. `reglement-demo-hygiene` · Article 6 : Le non-respect de la chaîne du froid est puni d'une amende pouvant atteindre 5 000 dinars, et de la fermeture temporaire de l'établissement en cas de récidive.

**Cause probable :** Le système ne transmet au LLM que k = 5 passages. La phrase « pas d'autres amendes » concerne donc seulement les passages consultés, pas l'ensemble du corpus. La fermeture temporaire est aussi présentée comme si elle faisait partie de l'amende.

**Analyse :** Les trois amendes citées sont justes, mais l'affirmation d'exhaustivité n'est pas garantie. Ce risque est propre aux questions de type liste ou « toutes les… ». Amélioration : augmenter k pour ce type de question, ou nuancer la formulation (« dans les passages consultés »).

## Cas 10 : Citations sans rapport avec la réponse

**Question :** Quel texte est le plus récent ?
**Attendu :** réponse d'impossibilité sans citation : les textes ne sont pas datés dans les extraits
**Réponse obtenue :** « Les textes ne sont pas datés dans les extraits fournis. Il n'est donc pas possible de déterminer lequel est le plus récent. », avec trois sources : `loi-demo-protection-donnees` · Article 9, `decret-demo-securite-si` · Article 3 et Article 4
**Étape fautive :** génération (LLM)

**Cause probable :** Le modèle cite par habitude, même quand sa réponse ne s'appuie sur aucun extrait. Rien dans le prompt ne distingue « citer ce que j'utilise » de « citer ce que j'ai reçu ».

**Analyse :** Le fond de la réponse est correct, mais des sources affichées sans rapport avec la question donnent une fausse impression de justification. Dans un outil de recherche réglementaire, une source citée doit toujours soutenir l'affirmation. Amélioration : consigne « cite uniquement les extraits que tu utilises réellement » et aucune citation pour une réponse d'impossibilité.

## Cas 11 : Caractère mal décodé dans la circulaire

**Question :** aucune (visible dans les passages consultés)
**Attendu :** « CHAPITRE II – EXÉCUTION ET RECOURS » et « CHAPITRE I – DISPOSITIONS GÉNÉRALES »
**Réponse obtenue :** « CHAPITRE II ? EXÉCUTION ET RECOURS » et « CHAPITRE I ? DISPOSITIONS GÉNÉRALES »
**Étape fautive :** extraction du texte

**Cause probable :** Le tiret long est mal décodé à la lecture de ce fichier. Seule la circulaire est concernée, et c'est aussi le seul texte avec des numéros de page, donc probablement un PDF. Les autres textes affichent correctement le tiret « – ».

**Analyse :** L'erreur n'affecte pas le contenu des réponses, mais elle dégrade les références affichées à l'utilisateur et trahit un problème d'encodage qui pourrait toucher d'autres caractères (accents, guillemets) dans d'autres fichiers. Amélioration : identifier le caractère exact dans le fichier, normaliser le texte à l'extraction (normalisation Unicode, remplacement explicite) et ajouter un test qui vérifie l'absence du caractère `?` dans les titres.
