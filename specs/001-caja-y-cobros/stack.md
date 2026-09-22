# Stack — Spec 001: envío del comprobante de venta por correo (RF-17 a RF-20)

**Estado:** aprobado (Rolando, 2026-09-22).

## Alcance de esta evaluación

RF-17/18/19/20 de `spec.md`: al completar un cobro sin factura formal, si el cajero
captura el email del cliente, se envía un comprobante interno (sin valor fiscal SIFEN)
a esa dirección; si no hay email no se envía nada y el cobro no se bloquea; si no hay
internet al momento de enviar, el envío se encola (Celery+Redis, ya resuelto por RF-20 /
RF-37) y se completa al reconectar.

Lo que decide esta evaluación es **un solo punto**: por dónde sale efectivamente el
correo hacia el cliente — mecanismo de transporte y desde qué infraestructura se
despacha. Todo lo demás (cola, reintentos, no bloquear el cobro <500ms) ya está resuelto
arquitectónicamente y no se re-evalúa acá.

**Fuera de re-evaluación** (fijado por ADRs previos, ver `docs/ARCHITECTURE.md`): Django
+ PostgreSQL, single-tenant, topología híbrida edge, Guaraní entero, UUID PKs,
append-only, terceros detrás de interfaz propia, Django templates + HTMX + Alpine.js,
Celery + Redis, service worker para N3.

## Candidatos

### A — SMTP directo desde el edge box (cuenta SMTP de terceros, ej. Gmail/Workspace, vía `EMAIL_BACKEND` estándar de Django)

Cada local envía su propio correo, desde su propio edge box, con su propia cuenta SMTP
(Gmail/Google Workspace u otro proveedor de correo genérico), usando el backend SMTP que
Django trae de fábrica.

### B — Proveedor transaccional de email vía API, integrado detrás de una interfaz propia (Amazon SES, Postmark, Mailgun u otro)

Cada edge box (o, más adelante, un despachador central) llama a la API de un proveedor
transaccional especializado en correo, encapsulado detrás de un puerto propio
(`notifications/providers/base.py`, siguiendo el mismo patrón que `payments/gateways` y
`billing/providers`), de forma que el proveedor concreto se pueda cambiar sin tocar el
dominio.

### C — Despacho diferido desde el componente en la nube (la réplica ya prevista en la arquitectura)

El edge box local solo encola la solicitud de envío en su cola local (esto ya ocurre por
RF-20, sin importar cuál de A/B se use como transporte final). En vez de que cada edge
box despache el correo directamente a internet, el envío efectivo lo hace la nube
central, con un solo remitente/dominio consolidado para todos los locales, usando un
proveedor transaccional vía API (opción B ejecutada centralizadamente en vez de por
edge box).

Nota: C no es alternativa a B, es una decisión de **dónde** se ejecuta B (en cada edge box
vs. en la nube). Se evalúa como candidato propio porque cambia radicalmente los otros
ejes (operabilidad, escalabilidad, reversibilidad), y porque la spec de esta feature no
prejuzga la ubicación del despachador — solo exige que el envío no bloquee el cobro y
que se reintente al reconectar, algo que tanto A+edge, B+edge como B+nube cumplen.

## Evaluación

### Fit de negocio (incluye modos de falla)

- **A (SMTP directo, edge)**: funciona mientras la cuenta SMTP del proveedor de correo
  genérico no la marque como sospechosa. Modo de falla característico: una cuenta Gmail
  personal/Workspace usada para envío automatizado dispara los límites de tasa de Gmail
  y, más grave, cualquier bloqueo o cambio de contraseña en esa cuenta corta el envío
  sin aviso hasta que alguien lo note. El fallo es silencioso desde el punto de vista
  del negocio: el cobro se completa igual (correcto, RF-20 no bloquea), pero el cliente
  nunca recibe su comprobante y nadie en el local se entera hasta que un cliente
  reclama.
- **B (API transaccional, edge)**: el proveedor está diseñado para este caso de uso
  (correo transaccional, no bulk/marketing), con manejo explícito de bounces, quejas y
  reputación. El modo de falla es más visible: la API devuelve error estructurado
  (credenciales, dominio no verificado, cuota agotada) que se puede loguear y alertar,
  en vez de un buzón que deja de responder sin explicación.
- **C (despacho vía nube)**: mismo proveedor y garantías que B, pero agrega una
  dependencia nueva: si la réplica en la nube está caída o desincronizada, el correo no
  sale aunque el edge box tenga internet propio. Esto es un modo de falla que la spec no
  tiene hoy (el sync a la nube es best-effort, no es la ruta crítica de ningún RF de
  caja). Contradice parcialmente el principio 1 de la constitución en su espíritu — no
  "el negocio no cobra", pero sí "una función que debería depender solo del edge queda
  atada a un componente adicional que no necesita para nada más en esta spec".

### Seguridad por diseño / por defecto

- **A**: la contraseña o token de la cuenta SMTP vive en la configuración del edge box
  de cada local. Si hay N locales, hay N credenciales de correo, cada una gestionada
  informalmente (una cuenta Gmail creada "para el sistema"). Nada por defecto: no hay
  SPF/DKIM/DMARC alineados a un dominio propio salvo que alguien los configure a mano
  por local, y usar el dominio de un proveedor de correo genérico para autenticar envíos
  automatizados masivos-por-local es exactamente el patrón que los filtros antispam
  penalizan.
- **B**: el proveedor transaccional soporta SPF/DKIM/DMARC de forma nativa y espera que
  se verifique un dominio propio del negocio (o del producto) para firmar los envíos.
  Detrás de una interfaz propia (como ya exige `docs/ARCHITECTURE.md` para Bancard y
  SIFEN), las credenciales de API se guardan una vez por instancia, con alcance acotado
  a "enviar correo", nada más.
- **C**: mismo nivel de seguridad en el transporte que B, con una ventaja adicional: la
  credencial del proveedor transaccional vive **una sola vez**, en la nube, no
  replicada en cada edge box. Menos superficie de exposición si un edge box es
  comprometido físicamente (constitución, principio 5: mínimo privilegio, mínimo dato).

### Escalabilidad (dónde rompe y a qué volumen)

- **A**: rompe temprano. Gmail SMTP limita a 100 envíos/día por cuenta gratuita vía SMTP
  automatizado (500 destinatarios/día en total, Google Workspace sube a 2000
  destinatarios/día) [verificado por búsqueda web, sep. 2026]. Con "algunas decenas a un
  par de cientos de comprobantes por día" declarado en el contexto, un local ya puede
  estar al límite o superarlo en el escenario alto, y no hay forma de subir ese límite
  sin cambiar de plan/proveedor.
- **B, ejecutado por edge box**: cada local tiene su propia cuota de API,
  independiente de los demás — no comparten límite entre locales. Amazon SES en modo
  sandbox limita a 200 mensajes/24h y 1 mensaje/segundo hasta pedir "production access"
  (aprobación manual de AWS, ~24h, sube a 50.000/día); una vez en producción, el volumen
  de un solo restaurante no es un problema real [verificado, sep. 2026]. El problema de
  escala real es otro: si esto crece a decenas de locales, cada uno resolviendo su
  propio dominio verificado, sus propias claves DKIM y su propia reputación de envío,
  es trabajo operativo que se multiplica por local en vez de centralizarse.
- **C**: un solo dominio/remitente para todos los locales significa una sola reputación
  que gestionar, un solo lugar donde subir el volumen contratado con el proveedor, y el
  volumen agregado de decenas de locales (unos pocos miles de correos/día en el peor
  caso) sigue siendo un volumen modesto para cualquier proveedor transaccional serio.
  Rompe distinto: si un local abusa (o un bug genera un loop de reenvíos), afecta la
  reputación del dominio compartido de *todos* los locales — es el motivo por el que
  proveedores como SES exigen manejo explícito de bounces/quejas antes de dar acceso de
  producción.

### Operabilidad (quién mantiene esto un sábado a las 11pm en un restaurante en Paraguay)

- **A**: si la cuenta Gmail pide verificación en dos pasos, cambia de contraseña, o
  Google decide que el patrón de envío es sospechoso, el envío de comprobantes se corta
  sin que nadie en el sistema lo sepa — no hay panel de estado de entregabilidad, no hay
  alertas de bounce. El dueño (un desarrollador solo) se entera por un cliente que
  reclama no haber recibido nada, días después. Nada que operar un sábado a las 11pm
  porque no hay nada que lo avise esa noche.
- **B (edge)**: la API devuelve error explícito y logueable (dominio no verificado,
  cuota, credencial inválida); se puede alertar por el mismo canal que ya se usa para
  otras fallas de sync. Pero el dueño tiene que mantener N configuraciones de dominio
  verificado y N credenciales, una por local, si esto escala.
- **C**: un solo panel de proveedor, una sola configuración de dominio, una sola cola de
  reintentos a nivel plataforma para observar. Para un desarrollador solo manteniendo
  múltiples locales, esto es la diferencia entre revisar un dashboard y revisar N
  dashboards. Es la opción con menos superficie operativa a mediano plazo, aun cuando
  agrega la dependencia de la nube al camino del envío (ver "fit de negocio").

### Fit de equipo (el dueño es un desarrollador solo, no un equipo grande)

- **A**: parece la más simple al inicio (una cuenta de correo, `EMAIL_BACKEND` de
  Django, cero librerías nuevas), pero esa simplicidad es ilusoria: en cuanto un ISP
  marca el remitente como spam, el dueño solo tiene que depurar un problema de
  reputación de correo sin herramientas — no es un problema de código, es un problema de
  relación con Google, y ahí un desarrollador solo tiene poco margen de maniobra.
- **B**: requiere una integración adicional (SDK o llamada HTTP al proveedor, manejo de
  webhooks de bounce si se quiere ser prolijo) pero es trabajo de una sola vez, bien
  documentado, con soporte del proveedor. Encaja con el patrón que el proyecto ya usa
  para Bancard/SIFEN (interfaz propia sobre un proveedor externo), así que no es un
  patrón nuevo a aprender.
- **C**: mismo trabajo de integración que B, pero además requiere que el despachador
  central (la réplica en la nube) tenga un rol activo — hoy la nube es "réplica,
  analítica, respaldo y acceso remoto" (`docs/ARCHITECTURE.md`, sección 1), no un
  servicio con responsabilidades operativas propias. Convertirla en despachador de
  correo es una responsabilidad nueva que el dueño tiene que diseñar y mantener (¿qué
  pasa si la nube está caída y el edge box tiene su propia salida a internet? ¿la cola
  se drena localmente como fallback, o espera indefinidamente a la nube?). Para un
  equipo de una persona, en la fase actual (un solo restaurante, spec 001 apenas se
  está implementando), es una pieza de infraestructura adicional a diseñar y operar
  antes de tener un segundo cliente que la justifique.

### Reversibilidad (costo de salir si esto estuvo mal)

- **A**: barata de abandonar en código (es un `EMAIL_BACKEND` de Django, se cambia en
  una línea de configuración) pero cara en confianza: si ya se quemó la reputación de
  una cuenta de correo o de un dominio, ese daño no se revierte cambiando de backend.
- **B (edge)**: al estar detrás de una interfaz propia (`notifications/providers/base.py`
  o similar), cambiar de proveedor transaccional es exactamente el mismo costo que
  cambiar de facilitador de pagos o de SIFEN — se implementa un nuevo adaptador, el
  dominio no se toca. Esto es barato de revertir por diseño, no por suerte.
- **C**: la interfaz sigue siendo la misma que B (el proveedor detrás del puerto no
  cambia), pero mover el despacho de "cada edge box" a "la nube central" es un cambio de
  topología, no solo de configuración: hay que decidir qué pasa con la cola existente en
  cada edge box, cómo se sincroniza el estado "enviado/pendiente" entre edge y nube, y
  quién es la fuente de verdad de si un comprobante ya salió. Es más caro revertir un
  cambio de topología que un cambio de proveedor.

## Recomendación

**Candidato B: proveedor transaccional de email vía API, ejecutado desde el edge box
local, detrás de una interfaz propia** (`notifications/providers/base.py`), con Amazon
SES como proveedor concreto inicial.

Por qué SES y no Postmark/Mailgun como proveedor concreto: para el volumen de un
restaurante individual (decenas a un par de cientos de comprobantes/día) el costo es
irrelevante en cualquiera de los tres (SES a USD 0,10 por 1.000 correos; Postmark con
plan gratuito de 100/mes y planes pagos desde USD 15/mes por 10.000; Mailgun con plan
gratuito de ~100/día) [verificado por búsqueda web, sep. 2026]. La razón para preferir
SES es operativa: al estar ya en el ecosistema AWS es razonable para el ADR de
infraestructura general del proyecto (backups/nube, aunque eso es una decisión fuera de
esta spec), y su modo sandbox (200 mensajes/24h, 1/seg, hasta pedir acceso de
producción) [verificado] es suficiente para desarrollo y para el primer local en
producción mientras se tramita el acceso completo. Esto queda como recomendación de
proveedor, no como restricción dura: la interfaz propia permite cambiar a Postmark o
Mailgun sin tocar el dominio si SES no encaja en la práctica (ej. si el trámite de
"production access" de AWS se demora o se rechaza).

**Alternativa descartada: A (SMTP directo con cuenta de correo genérica).** Se descarta
porque falla exactamente en el eje que más importa para esta spec: entregabilidad
silenciosa. Un comprobante que no llega y no se sabe que no llegó viola en la práctica
el espíritu de RF-18 ("el sistema enviará el comprobante") aunque el cobro en sí nunca
se bloquee (RF-19/20 sí se cumplen formalmente). Es la opción más simple de escribir y la
peor de operar sin que nadie lo note — el patrón clásico de "funciona en la demo, falla
en producción sin avisar".

**Nota sobre dominio y correo corporativo propio (dato agregado por Rolando el
2026-09-22, aún sin fecha ni proveedor definido).** El restaurante tendrá más adelante
su propio dominio, hosting y correo corporativo. Esto no cambia la recomendación —
mejora su base: el candidato B ya requiere verificar un dominio propio para
SPF/DKIM/DMARC (ver "Restricciones que esta elección impone al plan"), así que cuando el
dominio exista, el paso pendiente es simplemente verificarlo en el proveedor
transaccional elegido y usar una dirección propia (ej. `pedidos@sudominio.com.py`) como
remitente — sin tocar el adaptador ni el dominio de negocio, porque el proveedor
concreto vive detrás de la interfaz propia. Importante: un correo corporativo gestionado
(Google Workspace, Microsoft 365 u otro buzón para uso humano) **no reemplaza** al
proveedor transaccional del candidato B aunque comparta el mismo dominio — un buzón
pensado para correspondencia humana no está diseñado para el volumen ni el patrón de
envío automatizado de comprobantes, y reintroduciría el mismo riesgo de fallo silencioso
del candidato A si se usara como transporte. El correo corporativo sirve para atención al
cliente y comunicación humana del negocio; el envío de comprobantes sigue por SES (u otro
proveedor transaccional) autenticado con el dominio propio una vez que exista.

**C (despacho vía nube) no se descarta, se pospone.** Es arquitectónicamente más
correcto para el escenario de "decenas de locales" descrito en el contexto — un solo
remitente, una sola reputación, un solo lugar donde operar. Pero esta spec (001) es para
un solo restaurante, y la nube hoy no tiene responsabilidades operativas activas
(`docs/ARCHITECTURE.md`: "réplica, analítica, respaldo y acceso remoto"). Convertirla en
despachador de correo es una decisión de plataforma que afecta a todos los locales a la
vez, no algo que deba decidirse dentro de la spec de un único restaurante. Como B ya usa
una interfaz propia sobre el proveedor transaccional, migrar de "cada edge box despacha"
a "la nube despacha" es, cuando llegue el momento, un cambio de *quién* llama al mismo
adaptador — no de qué adaptador se usa. Queda anotado como candidato a revisar cuando
exista un segundo cliente real, no antes.

## Restricciones que esta elección impone al plan

- Se define un puerto propio `notifications/providers/base.py` (o ubicación equivalente
  dentro de la app que gestione notificaciones) que el dominio invoca sin conocer el
  proveedor concreto — mismo patrón que `payments/gateways/base.py` y
  `billing/providers/base.py` ya establecido en `docs/ARCHITECTURE.md`.
- El envío se dispara como tarea Celery encolada al completar el cobro (RF-17/18), nunca
  de forma síncrona en la vista — el NFR de <500ms en el registro del cobro no admite
  esperar una respuesta HTTP externa.
- El adaptador SES concreto vive en `infra`/`notifications`, no en `cash` ni en
  `payments`: la app de caja solo sabe que existe "un envío de comprobante pendiente",
  no cómo se transporta.
- Requiere verificar un dominio propio del proyecto (no una cuenta de correo genérica)
  para firmar SPF/DKIM/DMARC — esto es una tarea de infraestructura a resolver antes de
  implementar RF-18, no parte del código de la spec en sí.
- Mientras la cuenta esté en modo sandbox de SES, solo se pueden enviar correos a
  direcciones verificadas — el plan de implementación debe prever pedir acceso de
  producción a AWS con margen de al menos 24-48h antes de cualquier demo con clientes
  reales o direcciones no verificadas.
- Los errores de envío (dominio no verificado, cuota, bounce) deben loguearse como
  evento de auditoría o alerta operativa — no deben fallar silenciosamente. Esto es
  además coherente con el principio 5 de la constitución (toda acción sensible deja
  rastro).
- La decisión de mover el despacho a la nube (candidato C) queda explícitamente abierta
  para revisión futura y no debe cerrarse por default ni por costumbre cuando aparezca
  el segundo local — requiere su propia evaluación cuando llegue ese momento.

## Fuentes verificadas (búsqueda web, septiembre 2026)

- Amazon SES: USD 0,10 por 1.000 correos enviados fuera de EC2; sin free tier específico
  de SES para cuentas nuevas desde jul. 2025 (créditos generales de AWS en su lugar);
  modo sandbox 200 mensajes/24h, 1 msg/seg; producción hasta 50.000/día, 14 msg/seg tras
  aprobación manual de AWS (~24h).
- Mailgun: plan gratuito ~100 correos/día (~3.000/mes), retención de logs de 1 día.
- Postmark: plan gratuito de desarrollo, 100 correos/mes sin vencimiento; planes pagos
  desde USD 15/mes por 10.000 correos (reestructurado a inicios de 2026).
- Gmail SMTP: cuenta gratuita limitada a 100 envíos automatizados/día vía SMTP (500
  destinatarios/día en total); Google Workspace hasta 2.000 destinatarios/día.

No se encontró información específica y verificable sobre deliverability o soporte
diferenciado de estos proveedores para Paraguay/LatAm en particular — se marca como
`[NECESITA ACLARACIÓN]` si esto resulta relevante más adelante (ninguno de los tres
publica métricas de entregabilidad por país). La recomendación no depende de ese dato:
se basa en límites, costo y patrón arquitectónico ya establecido en el proyecto.

---

**Aprobado por Rolando el 2026-09-22** (candidato B, SES como proveedor inicial, detrás
de interfaz propia). Habilita `/sdd-plan`.
