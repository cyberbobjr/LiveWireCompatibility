# ADR-003 — Profondeurs B42 des machines d'Artel Manufactory

| Champ | Valeur |
|---|---|
| Identifiant | `ADR-003-PROFONDEURS-MACHINES-ARTEL` |
| Date de création et de mise à jour | 2026-11-20 (D04 ajoutée le même jour : tous les profils) |
| Statut | Accepté (2026-11-20) |
| Avancement | voir le [plan 003](../ADR-plans/plan-003-profondeurs-machines-artel.md) |
| Décideur | l'utilisateur |
| Portée | `batman_LiveWireCompatibility` : `common/media/depthmaps/DEPTH_Artel.png`, `common/media/tileGeometry.txt`, outils `tools/depthlib.py`, `tools/build_depth.py`, `tools/check_depth.py` (d'abord `tools/build_artel_depth.py`, remplacé par D04) ; les mods cibles et Live Wire ne changent pas |
| Documents liés | [ADR-002](termines/002-interrupteur-et-coupure-des-machines.md), `.claude/pz-knowledge/custom-tiles-entities.md` (profondeur B42 d'une tuile de mod) |
| Références | `TilesetDepthTexture.mergeTileset` (`TilesetDepthTexture.java:196-206`), `TileDepthTexture.load` (`:155-175`), `IsoSprite.java:962-966`, `TileDepthTextureManager.initMergedTilesets` (`:82-88`) |
| Origine | demande de l'utilisateur du 2026-11-20 : le lyophilisateur Artel n'a aucune couleur dans « Afficher les consommateurs » de face, mais il est coloré quand le joueur est derrière ; « on ne peut pas ajouter nous même la carte de profondeur pour corriger ? » — « oui » |

## Contexte

Diagnostic en jeu (2026-11-20) : Live Wire envoie bien la ligne du lyophilisateur et pose sa couleur
(`isHighlighted` vrai, couleur rouge 0,85), mais le jeu ne la dessine pas de face ; un vert forcé à la main et le
survol du menu contextuel ne s'affichent pas non plus. Derrière la machine (tuile `solidtrans` redessinée
translucide à chaque image), la couleur apparaît. Statiquement : la carte `DEPTH_Artel.png` d'Artel ne contient des
texels que pour les tuiles 200 à 223 ; toutes ses machines (36, 37, 52, 53, 56, 58, 104, 107, 112 à 143, 121 à 124)
ont une case vide et prennent la profondeur par défaut du moteur. Le lien exact entre profondeur par défaut et passe
de surbrillance n'est pas prouvé (hypothèse forte).

Le moteur fusionne les cartes de profondeur des mods case par case : une case vide d'un mod est remplie par la case
non vide d'un autre (`TilesetDepthTexture.mergeTileset`). Les dimensions fusionnées prennent le minimum des lignes et
colonnes des cartes.

## Décisions

- **D01 — Ce mod fournit les profondeurs des machines d'Artel**, dans sa propre carte
  `common/media/depthmaps/DEPTH_Artel.png` et le fichier minimal `common/media/tileGeometry.txt` (sans lui la carte
  n'est pas chargée). Seules les cases des machines facturées par le profil Artel sont remplies ; toutes les autres
  restent vides, donc Artel garde les siennes (200 à 223). La carte a exactement les dimensions de celle d'Artel
  (fusion au minimum des lignes). Aucun fichier d'Artel n'est remplacé ni recopié.
- **D02 — Profondeur générée par un bloc ajusté à la silhouette.** Les machines n'ont pas de modèle 3D publié : chaque
  sprite est assimilé au plus petit bloc posé au sol (emprise rectangulaire dans la case, hauteur) dont la projection
  couvre ses pixels. Projection et codage du moteur (base de connaissances) : écran `sx = 64 (wx − wy) + 64`,
  `sy = 32 (wx + wy) + 192 − 192 wz` (case 128 × 256, wz en niveaux) ; profondeur `1 − 0,25 (wx + wy) − 0,5 wz` ;
  texel `floor(profondeur × 255)` en R, G, B, alpha 255. Un pixel du sprite hors du bloc prend la plus lointaine des
  profondeurs voisines : aucun pixel dessiné n'est privé de texel.
- **D03 — Outil local, hors CI.** `tools/build_artel_depth.py` lit le pack d'Artel en lecture seule (lecteur
  `pz-sprite-forge`) et écrit la carte ; il rapporte, par tuile, le bloc retenu et les pixels sans texel (attendu 0).
  À relancer après une mise à jour des sprites d'Artel. Si Artel publie un jour ses propres profondeurs, la carte de ce
  mod n'a plus d'effet sur ces cases (la première case non vide gagne) et peut être retirée.

- **D04 — Généralisation à tous les profils** (2026-11-20, demande de l'utilisateur après le contrôle de tous les
  profils : 40 sprites sans aucune profondeur dans Project Arcade, Machinery et Plysken Weather Station). Le même
  calcul fournit une carte `DEPTH_<tileset>.png` par jeu de tuiles concerné, aux dimensions de la carte existante du
  jeu de tuiles quand il y en a une. Ne sont remplis que les sprites **sans aucune profondeur** (ni case non vide, ni
  renvoi) : un sprite qui a une profondeur, même incomplète, la garde. Mesure à l'appui : des cartes du jeu lui-même
  laissent des pixels opaques hors profondeur (hotte `appliances_cooking_01_68` : 130), et le bloc est plus grossier
  qu'une profondeur dessinée pour le sprite. `tools/check_depth.py` échoue pour un sprite sans profondeur et signale
  en note les pixels opaques non couverts. `tools/build_artel_depth.py` devient `tools/depthlib.py` (calcul, sources
  fusionnées comme le moteur, lecture des packs) et `tools/build_depth.py`.

## Conséquences

- La surbrillance de « Afficher les consommateurs » et du menu contextuel doit apparaître de face (à confirmer en
  jeu) ; l'occultation des machines (ce qui passe devant ou derrière) devient plus juste qu'avec la case entière.
- Un bloc est une approximation : un détail saillant de la machine peut être occulté un peu tôt ou un peu tard.
- Sans Artel actif, la carte est chargée mais ne sert à aucun sprite.
