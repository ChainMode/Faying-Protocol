# Vision Humaine

Le Chapitre 2 a déjà nommé la proposition : une fois qu'un Fay est interposé dans l'action numérique, l'initiateur et le porteur de la responsabilité développent une fissure structurelle. Le Faying Protocol fournit la forme du contrat, mais que le contrat puisse réellement recevoir la responsabilité dépend d'un engagement plus en amont :

> **Chaque action Fay doit se produire dans le rayon que son Human Prime peut « voir ».**

« Voir » ici n'est pas visuel au sens physique, mais un concept généralisé : le Human Prime, l'individu ou l'organisation auquel le Fay est attribué, peut confirmer à tout moment que le Fay opère sous tutelle.

Cette « vision » généralisée est appelée **Human View**. Ce n'est pas un champ, un interrupteur ou une API du Faying Protocol ; c'est une valeur à laquelle chaque décision technique du Faying Protocol doit obéir. Si un champ, un message ou une conception de machine d'état laisse un Fay dériver hors de Human View, cette conception n'est pas permise au niveau du blueprint, peu importe sa commodité en ingénierie.

## Human View n'est pas la vue physique

La vue physique, c'est « je peux voir ce drone en ce moment », « la caméra a attrapé le robot à l'instant ». La vue physique est contrainte par la lumière, la distance, l'occlusion et l'attention. Dans de nombreux scénarios, elle ne peut tenir du tout — un Human Prime ne peut pas surveiller tous ses Fays en permanence.

Human View décrit une confirmabilité structurelle :

- elle n'exige pas que le Human Prime regarde le Fay en ce moment ;
- mais elle exige que chaque fois que le Human Prime veut vérifier, il puisse confirmer immédiatement si le Fay est sous tutelle ;
- et elle exige que les actions du Fay laissent une trace traçable, afin que « ce qui vient de se passer, et à qui cela appartient » puisse être confirmé rétroactivement.

Autrement dit, Human View ne se soucie pas d'« être vu » mais de « **pouvoir être vu** ». C'est la clé par laquelle elle peut tenir à travers les innombrables scénarios fortement automatisés — essaims de drones, robots domestiques, Fays de processus d'entreprise.

## Quatre anti-propositions : quatre situations interdites

La manière la plus puissante de définir une valeur est de dire ce qu'elle interdit. Human View interdit explicitement les quatre situations suivantes, appelées les **quatre anti-propositions** de Human View.

**Non autorisé** (Unauthorized) — le Fay mène des actions sans avoir obtenu l'autorisation du Human Prime. « Obtenir l'autorisation » est un acte vérifiable, et non un état que le Fay revendique de lui-même. Un Fay profondément convaincu que « le Human Prime serait sûrement d'accord avec cela » n'est pas autorisé.

**Non intentionnel** (Unintended) — le Fay détient une autorisation légitime, mais l'action spécifique présente n'a pas été l'objet d'une expression d'intention par le Human Prime, et diverge de l'intention présente du Human Prime. L'autorisation résout « ceci est-il autorisé à bouger » ; l'expression d'intention résout « ce mouvement particulier ». Human View exige que les deux tiennent simultanément.

**Non conscient** (Unaware) — le Fay est à la fois autorisé et a fait l'objet d'une expression d'intention, mais en fait le Human Prime ne peut, à un coût raisonnable, prendre connaissance de ce que le Fay fait. Cette situation n'est souvent pas le Fay dissimulant activement les choses mais un défaut dans la conception du protocole — il empêche l'information de remonter du côté du Human Prime. Human View prend la « joignabilité de l'information » comme condition dure de la relation de tutelle.

**Hors de contrôle** (Out-of-Control) — le Human Prime est déjà conscient, mais ne peut plus intervenir en temps réel, par exemple le Fay refuse les commandes de révocation, refuse d'avorter les tâches, refuse de ralentir. Cette situation est la forme finale des trois autres : lorsqu'un Fay n'a pas besoin de chercher une autorisation, n'a pas besoin de divulguer son action, et n'a pas besoin d'accepter l'intervention, la « tutelle » n'est plus qu'un nom. Human View exige que le chemin d'intervention soit toujours ouvert.

Les quatre anti-propositions ne sont pas une liste mutuellement exclusive mais des frontières de défaillance progressivement plus profondes : Non autorisé est une défaillance à l'entrée, Non intentionnel est une défaillance pendant le processus, Non conscient est une défaillance dans la rétroaction, Hors de contrôle est une défaillance à la dernière porte. Le Faying Protocol doit tenir la ligne aux quatre niveaux à la fois pour assumer la valeur de Human View.

## S'applique également à iFay et coFay

Human View n'est pas une contrainte uniquement sur les Fays individuels (iFay) ; **elle s'applique également à iFay et coFay**.

Un iFay a une correspondance un-pour-un explicite avec un Human Prime spécifique ; la relation de tutelle est intuitive. Un coFay correspond généralement à une organisation, une équipe ou un rôle, et la relation de tutelle n'est pas naturellement claire. Cependant, précisément parce que l'extrémité d'attribution d'un coFay est souvent une organisation plutôt qu'une personne spécifique, les exigences de Human View doivent être exprimées encore plus explicitement : l'organisation doit, au niveau institutionnel, clarifier « qui est autorisé à exercer la tutelle au nom de l'organisation », sinon le coFay glisse en fait dans la zone grise « pas de personne responsable spécifique qui puisse maintenir la tutelle ».

Aucun Fay, qu'il soit iFay ou coFay, ne peut dériver hors de Human View au motif que « j'appartiens à une organisation, donc personne n'est spécifiquement en tutelle ». L'organisation a le devoir de faire atterrir le devoir de tutelle sur une personne ou un rôle spécifique. Ce n'est pas une question technique ; c'est une question de valeurs.

## Relation avec le Faying Protocol

Human View est une valeur au niveau du blueprint ; le Faying Protocol est la spécification de contraintes techniques qui porte cette valeur.

Human View répond à « pourquoi une certaine contrainte est nécessaire ». Le Faying Protocol répond à « comment cette contrainte est techniquement et fidèlement assumée ».

Si Human View est une charte, le Faying Protocol est l'ensemble du corps du droit fondamental qui fait atterrir la charte sur des organes d'exécution spécifiques, des procédures spécifiques et des identifiants spécifiques. Une charte sans porteur juridique dégénère en slogan ; un corps de droit qui s'écarte de la charte qu'il était censé porter devient la chose même contre laquelle la charte était censée s'opposer. Les deux doivent se calibrer mutuellement : lorsqu'une conception du Faying Protocol facilite la dérive d'un Fay hors de Human View, elle doit être rejetée, peu importe sa commodité en ingénierie ; lorsqu'un nouveau scénario rend Human View difficile à assumer sous le Faying Protocol existant, cela signifie que le Faying Protocol doit être mis à niveau, et non que Human View doit être concédée.

Le Chapitre 12 (Sémantique Duale de Faying) et le Chapitre 13 (Rogue Fay et Attribution de Responsabilité) recevront cette valeur au niveau de la forme du protocole : le Chapitre 12 explique comment la relation de tutelle est établie et maintenue ; le Chapitre 13 explique comment, une fois que la tutelle ne tient plus, le Fay doit s'arrêter. Ensemble, les deux sont l'atterrissage concret de Human View au niveau du protocole.
