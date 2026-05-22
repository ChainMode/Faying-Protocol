# Human View

Kapitel 2 hat die These bereits benannt: Sobald ein Fay in eine digitale Handlung dazwischengeschaltet wird, entwickeln Initiator und Träger der Verantwortung eine strukturelle Bruchlinie. Das Faying Protocol bietet die Vertragsform, doch ob der Vertrag Verantwortung tatsächlich aufnehmen kann, hängt von einer noch vorgelagerten Verpflichtung ab:

> **Jede Fay-Handlung muss innerhalb des Bereichs erfolgen, den ihr Human Prime „sehen" kann.**

„Sehen" meint hier nicht visuell im physischen Sinne, sondern ist ein verallgemeinerter Begriff: Der Human Prime, die Person oder Organisation, der der Fay zugeordnet ist, kann jederzeit bestätigen, dass der Fay unter Aufsicht operiert.

Dieses verallgemeinerte „Sehen" heißt **Human View**. Es ist kein Feld, kein Schalter und keine API im Faying Protocol; es ist ein Wert, dem jede technische Entscheidung im Faying Protocol gehorchen muss. Wenn irgendein Feld, irgendeine Nachricht oder irgendein Zustandsmaschinen-Design es einem Fay erlaubt, sich außerhalb von Human View zu entfernen, ist dieses Design auf Blueprint-Ebene nicht zulässig, egal wie bequem es ingenieurtechnisch ist.

## Human View ist nicht physische Sicht

Physische Sicht ist „ich kann diese Drohne gerade jetzt sehen", „die Kamera hat den Roboter gerade erfasst". Physische Sicht ist durch Licht, Distanz, Verdeckung und Aufmerksamkeit eingeschränkt. In vielen Szenarien kann sie schlicht nicht halten — ein Human Prime kann nicht alle seine Fays rund um die Uhr beobachten.

Human View beschreibt eine strukturelle Bestätigbarkeit:

- Sie verlangt nicht, dass der Human Prime den Fay gerade jetzt anschaut;
- aber sie verlangt, dass der Human Prime, wann immer er prüfen will, sofort bestätigen kann, ob der Fay unter Aufsicht steht;
- und sie verlangt, dass die Handlungen des Fay eine rückverfolgbare Spur hinterlassen, sodass „was gerade geschah und wem es gehört" rückwirkend bestätigt werden kann.

Mit anderen Worten: Human View kümmert sich nicht um „gesehen werden", sondern um „**gesehen werden können**". Das ist der Schlüssel, durch den sie über die unzähligen hochautomatisierten Szenarien hinweg halten kann — Drohnenschwärme, Heimroboter, Unternehmensprozess-Fays.

## Vier Antithesen: vier verbotene Situationen

Der wirkungsvollste Weg, einen Wert zu definieren, ist zu sagen, was er verbietet. Human View verbietet ausdrücklich die folgenden vier Situationen, genannt die **vier Antithesen** von Human View.

**Unautorisiert** — der Fay führt Handlungen aus, ohne eine Autorisierung des Human Prime erhalten zu haben. „Eine Autorisierung erhalten" ist eine verifizierbare Handlung, kein Zustand, den der Fay über sich selbst behauptet. Ein Fay, der zutiefst überzeugt ist, „der Human Prime würde dem sicher zustimmen", ist nicht autorisiert.

**Unbeabsichtigt** — der Fay hält eine legitime Autorisierung, doch die gegenwärtige spezifische Handlung ist vom Human Prime nicht intentional ausgesprochen worden und weicht von der gegenwärtigen Absicht des Human Prime ab. Autorisierung löst „darf dies sich bewegen"; Absichtsausdruck löst „diese spezifische Bewegung". Human View verlangt, dass beide gleichzeitig halten.

**Unkenntnis** — der Fay ist sowohl autorisiert als auch absichtsmäßig ausgedrückt, doch faktisch kann der Human Prime zu vertretbaren Kosten nicht erfahren, was der Fay tut. Diese Situation ist oft kein aktives Verbergen seitens des Fay, sondern ein Mangel im Protokolldesign — er verhindert, dass Information zur Seite des Human Prime zurückfließt. Human View nimmt „Erreichbarkeit der Information" als harte Bedingung der Aufsichtsbeziehung.

**Außer Kontrolle** — der Human Prime ist bereits informiert, kann aber nicht mehr in Echtzeit eingreifen, z. B. der Fay verweigert Widerrufsbefehle, verweigert das Abbrechen von Aufgaben, verweigert die Verlangsamung. Diese Situation ist die Endform der drei anderen: Wenn ein Fay keine Autorisierung mehr suchen, keine Handlung offenlegen und keine Intervention akzeptieren muss, bleibt von „Aufsicht" nur der Name. Human View verlangt, dass der Interventionspfad stets offen ist.

Die vier Antithesen sind keine sich gegenseitig ausschließende Liste, sondern progressiv tiefere Versagensgrenzen: Unautorisiert ist Versagen am Eintritt, Unbeabsichtigt ist Versagen während des Prozesses, Unkenntnis ist Versagen im Feedback, Außer Kontrolle ist Versagen am letzten Tor. Das Faying Protocol muss alle vier Ebenen gleichzeitig halten, um den Wert von Human View zu erfüllen.

## Gilt gleichermaßen für iFay und coFay

Human View ist keine Beschränkung allein für individuelle Fays (iFay); **sie gilt gleichermaßen für iFay und coFay**.

Ein iFay hat eine ausdrückliche Eins-zu-eins-Entsprechung mit einem spezifischen Human Prime; die Aufsichtsbeziehung ist intuitiv. Ein coFay entspricht gewöhnlich einer Organisation, einem Team oder einer Rolle, und die Aufsichtsbeziehung ist nicht von Natur aus klar. Doch gerade weil das Zuordnungsende eines coFay oft eine Organisation und keine spezifische Person ist, müssen die Anforderungen von Human View umso ausdrücklicher artikuliert werden: Die Organisation muss auf institutioneller Ebene klarstellen, „wer befugt ist, die Aufsicht im Namen der Organisation auszuüben", andernfalls gleitet der coFay faktisch in die Grauzone „keine spezifische verantwortliche Person, die die Aufsicht halten kann".

Kein Fay, ob iFay oder coFay, darf sich mit der Begründung „ich gehöre zu einer Organisation, also führt niemand spezifisch Aufsicht" außerhalb von Human View entfernen. Die Organisation hat die Pflicht, die Aufsichtspflicht auf eine spezifische Person oder Rolle niederzubringen. Dies ist keine technische Frage; es ist eine Werte-Frage.

## Verhältnis zum Faying Protocol

Human View ist ein Wert auf Blueprint-Ebene; das Faying Protocol ist die technische Beschränkungsspezifikation, die diesen Wert trägt.

Human View beantwortet „warum eine Beschränkung nötig ist". Das Faying Protocol beantwortet „wie diese Beschränkung technisch treu erfüllt wird".

Wenn Human View eine Verfassung ist, ist das Faying Protocol das gesamte Grundgesetz, das die Verfassung auf spezifische Vollzugsbehörden, spezifische Verfahren und spezifische Anmeldedaten landet. Eine Verfassung ohne rechtlichen Träger verkommt zur Parole; ein Gesetzeskorpus, der von der Verfassung abweicht, die er tragen sollte, wird zu eben dem, dem die Verfassung entgegentreten sollte. Beide müssen sich gegenseitig kalibrieren: Wenn ein Design des Faying Protocol es einem Fay erleichtert, sich außerhalb von Human View zu entfernen, muss es abgelehnt werden, egal wie bequem es ingenieurtechnisch ist; wenn ein neues Szenario es schwer macht, Human View unter dem bestehenden Faying Protocol zu erfüllen, bedeutet das, dass das Faying Protocol aufgewertet werden muss, nicht Human View nachgegeben werden darf.

Kapitel 12 (Duale Semantik von Faying) und Kapitel 13 (Rogue Fay und Verantwortungszuordnung) werden diesen Wert auf der Protokollform-Ebene aufnehmen: Kapitel 12 erläutert, wie die Aufsichtsbeziehung hergestellt und aufrechterhalten wird; Kapitel 13 erläutert, wie der Fay, sobald die Aufsicht nicht mehr hält, stoppen muss. Zusammen sind beide die konkrete Landung von Human View auf der Protokollebene.
