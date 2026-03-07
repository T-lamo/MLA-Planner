### Tableau de couverture par cas de test

| Cas | Scénario | Données seed |
| :--- | :--- | :--- |
| **A1** | u2 CONFIRME + PROPOSE dans PUBLIE | s6a CONFIRME / s6b PROPOSE sur P6 |
| **A2** | BROUILLON incomplet (not ready) | P5 : s5(50%) + s5b(0%) → filled=0/2 |
| **A3** | BROUILLON prêt à publier | P2 : s2 nb_req=2, 2 affectations → filled=1/1 |
| **A3** | PUBLIE + ANNULE + TERMINE présents | P1/P4/P6, P7, P3 |
| **B1** | Amos REFUSE dans un PUBLIE | s1c (7h-9h, P1) TENOR REFUSE |
| **B2** | Jean dans 2 ministères, rôles distincts | Louange : SON(P1/P2) + PIANO(P8) / Technique : SON+LUMIERE+VIDEO(P4/P5) |
| **B3** | Validation pôle ↔ ministère | Inchangé — déjà cohérent |
| **C1** | rate=100% (nb_req=2, 2 affectations) | s1a (P1), s8 (P8) |
| **C1** | rate=50% (nb_req=2, 1 affectation) | s1b (P1), s5 (P5), s1c (P1) |
| **C1** | rate=0% (nb_req=3, 0 affectation) | s5b (P5) |
| **C2** | Amos ≥3 PUBLIE sur ≥2 jours | s1a+s1b (J+7), s8 (J+14) |


### Done. Récapitulatif des comptes après make db-setup-back 

| Rôle | Username | Password |
| :--- | :--- | :--- |
| **Super Admin** | `superadmin` | `plan123!` |
| **Admin** | `amos` | `plan123!` |
| **Responsable MLA** | `jean` | `plan123!` |
| **Membre MLA** | `awa` | `plan123!` |