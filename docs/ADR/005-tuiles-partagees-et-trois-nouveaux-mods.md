# ADR-005 — Tuiles partagées entre profils ; Knox Working Machines, STFO 3T et CamRecorder

| Champ | Valeur |
|---|---|
| Identifiant | `ADR-005-TUILES-PARTAGEES-ET-TROIS-NOUVEAUX-MODS` |
| Date de création et de mise à jour | 2026-11-20 |
| Statut | Accepté (2026-11-20) |
| Avancement | voir le [plan 005](../ADR-plans/plan-005-tuiles-partagees-et-trois-nouveaux-mods.md) |
| Décideur | l'utilisateur |
| Portée | `batman_LiveWireCompatibility` : chargeur (`LWC_Profiles`), gardes, interrupteur ; profils Machinery et Computer Mod (tuiles partagées) ; nouveaux profils Knox Working Machines, STFO, CamRecorder ; cartes de profondeur |
| Documents liés | [ADR-001](001-compatibilite-mods-tiers.md) (D05 : analyse avant profil), [ADR-002](termines/002-interrupteur-et-coupure-des-machines.md), [ADR-003](003-profondeurs-machines-artel.md), [ADR-004](004-signaler-les-changements-a-livewire.md) |
| Références | rapports d'analyse du 2026-11-20 : `annexes/recherches/knox-working-machines.md`, `stfo-3t.md`, `camrecorder.md` |
| Origine | demande de l'utilisateur du 2026-11-20 : « ajoute la compatibilité avec les mods suivants » (Workshop 3841890337, 3838240933, 3840702720) |

## Contexte

Analyse D05 (statique, lecture seule) des trois mods :
- **Knox Working Machines** (3841890337, `KnoxWorkingMachines`) donne un usage électrique à des tuiles **vanilla** de
  machines-outils : 24 d'entre elles sont aussi déclarées par le profil **Machinery**, et pas toujours pour la même
  machine (`industry_03_48` à `55` : presse hydraulique pour Machinery, fraiseuse pour Knox). Knox fait de chaque tuile une
  section indépendante (tour en 3 sections), Machinery un meuble de plusieurs cases.
- **CamRecorder** (3840702720) fait de l'ordinateur de bureau vanilla (`appliances_com_01_72` à `75`) un PC de
  surveillance, tuiles déjà déclarées par le profil **Computer Mod**.
- **STFO 3T** (3838240933, `STFO`) a ses propres appareils, alimentés par le secteur **ou** une batterie de voiture placée
  dans l'appareil.

Live Wire refuse un sprite déclaré deux fois (`duplicate_sprite`) : avec deux mods actifs, le second profil perdait ses
machines, et le test d'unicité interdisait ces profils.

## Décisions

- **D01 — Tuiles partagées.** Un consommateur de profil peut porter `shared = "<Id>"` et `owns = function(o) -> bool`.
  Le chargeur inscrit **un seul** consommateur Live Wire par `shared` (id = `<Id>`, sprites = union des profils actifs).
  Pour chaque objet, le membre est le premier dont `owns(o)` est vrai (ordre des profils), sinon le membre sans `owns`
  (repli). Ce membre décide de tout : consommation, interrupteur, gardes, nom. `LiveWireCompat.Profiles.consumerIdOf(o)`
  rend l'id du membre ; gardes, interrupteur et signalement l'utilisent à la place de l'id Live Wire. Un sprite ne peut
  être déclaré par deux profils que sous le même `shared`.
- **D02 — Machinery et Knox** partagent la perceuse à colonne, les tours, le bloc `industry_03_48`-`63` et le touret
  (`owns` : données `movableData.Machinery` pour Machinery, entité `KWM_*` pour Knox). **Computer Mod et CamRecorder**
  partagent l'ordinateur de bureau (repli Computer Mod ; CamRecorder possède un PC dont `pzVideoConsoleEnabled` est posé).
  Les consommations publiées de Machinery et Computer Mod ne changent pas.
- **D03 — Knox Working Machines** : interrupteur du mod sur ses machines électriques (le mod n'en a aucun), coupure par
  les points d'entrée vanilla des stations (ouverture de la fenêtre, lancement et poursuite d'une fabrication) et par le
  menu du lavage auto ; consommations moyennes estimées.
- **D04 — STFO** : seule l'alimentation **secteur** est soumise à Live Wire (facturée, coupée) ; une batterie dans
  l'appareil continue de fonctionner. Interrupteur du mod pour les appareils sans interrupteur propre (électrificateur,
  détecteur, boîtier de portail) ; projecteurs et tourelle gardent le leur, signalé à Live Wire (ADR-004).
- **D05 — CamRecorder** : caméra de sécurité fixée (sur le secteur seulement, pas les caméscopes sur piles), caméra
  Imekagi, moniteurs et PC de surveillance ; interrupteurs propres du PC et des moniteurs signalés ; les téléviseurs
  vanilla sont déjà facturés par Live Wire.
- **D06 — Profondeurs** : `tools/build_depth.py` remplit les tuiles des nouveaux profils qui n'en ont pas (ADR-003).

## Conséquences

- Deux mods qui donnent un usage à la même tuile vanilla peuvent être actifs ensemble : chaque objet est facturé et coupé
  selon le mod qui l'a posé.
- Le cœur gagne `shared`/`owns` et `consumerIdOf` ; les tests d'unicité acceptent un sprite partagé sous le même `shared`.
