# Rapport d'erreurs : mode `hybrid`, k = 5

Questions : 32 · cas à analyser : 5 (dont 2 erreurs réelles)

| Type | Nombre |
|---|---|
| Question sans réponse acceptée à tort | 2 |
| Succès fragile (à surveiller) | 3 |

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

**Ton analyse :** _à compléter (pourquoi, et quelle amélioration proposer)._

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

**Ton analyse :** _à compléter (pourquoi, et quelle amélioration proposer)._

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

**Ton analyse :** _à compléter (pourquoi, et quelle amélioration proposer)._

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

**Ton analyse :** _à compléter (pourquoi, et quelle amélioration proposer)._

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

**Ton analyse :** _à compléter (pourquoi, et quelle amélioration proposer)._
