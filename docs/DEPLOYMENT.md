# DEPLOYMENT.md

Esqueleto. Se completa en el handoff de la spec 001 (`/sdd-handoff`), con datos reales,
no con supuestos.

## Topología

Ver `ARCHITECTURE.md` §1. Dos destinos por cliente:

1. **Edge box** — mini PC en el local. Django + PostgreSQL + Redis. Fuente de verdad
   durante la operación.
2. **Nube** — réplica, analítica, respaldo y acceso remoto del administrador.

Single-tenant: una instancia y una base por cliente.

## Pendiente de definir

- [NECESITA ACLARACIÓN] Modelo de hardware del edge box y su costo por instalación.
- [NECESITA ACLARACIÓN] Proveedor de nube y región.
- [NECESITA ACLARACIÓN] Estrategia de respaldo: frecuencia, destino, cifrado, y prueba
  de restauración. Un respaldo que nunca se restauró no es un respaldo.
- [NECESITA ACLARACIÓN] Mecanismo de actualización remota del edge box.
- [NECESITA ACLARACIÓN] TLS entre terminales y edge box dentro de la LAN.

## Checklist previo a cada release

- [ ] `make ship` en verde
- [ ] Migraciones revisadas por `migration-reviewer`, con plan de aplicación
- [ ] Respaldo verificado antes de migrar
- [ ] `docs/PRIVACY.md` actualizado
- [ ] Variables de entorno nuevas documentadas en `.env.example`
- [ ] Procedimiento de rollback escrito y probado
- [ ] Ventana de aplicación acordada fuera del horario de servicio

## Rollback

<Se documenta con el primer release real.>
