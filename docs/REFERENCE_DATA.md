# LeadTools reference data

LeadTools stores external reference observations in PostgreSQL and serves only a
promoted last-known-good version. Calculator and page requests never wait on the
external provider.

## Current provider

The first provider is the World Bank Indicators API and the first indicator is
PA.NUS.PPP, the annual PPP conversion factor. It is purchasing-power context,
not a current foreign-exchange rate, freelancer market rate, tax rule or client
price recommendation.

The provider host and indicator are fixed in code. Country codes are an explicit
operator setting, limited to 50 ISO alpha-3 codes. Responses have a two-megabyte
limit, strict schema/value validation, bounded timeouts and two retries.

## Database and refresh

Apply migrations with the migrator role:

    python -m alembic -c alembic.ini upgrade head

Configure:

    REFERENCE_DATA_COUNTRIES=KEN,USA,GBR
    REFERENCE_DATA_MAX_AGE_DAYS=500
    REFERENCE_DATA_TIMEOUT_SECONDS=20

Run the explicit background refresh:

    python -m app.jobs.refresh_reference_data

A successful job prints only dataset/version/status/count metadata. A failed job
prints a categorized error, records a failed import run and exits nonzero. It
does not store raw provider responses or credentials.

The importer first records an audit run. It validates the complete provider
batch, computes a deterministic content checksum, stores immutable observations,
then promotes the dataset version in the same database transaction. A failed
provider or database operation does not replace an existing active version.
Re-importing identical content is idempotent.

Schedule this command as a separate monthly or weekly job in deployment. Do not
run it inside the web process startup and do not use the web service as a generic
URL fetcher.

## Read API

    GET /reference-data/ppp/{ISO3}

The response includes the geography, observation period, value and unit plus:

- current or stale freshness state;
- dataset and content version;
- provider and indicator;
- source and licence links;
- retrieval/source-update timestamps;
- the limitation statement.

No observation returns 404. An active dataset without a successful timestamp
fails closed. The endpoint caches a successful response for one hour.

## Verification

The deterministic suite covers provider retry, null/invalid observations,
idempotent imports, last-known-good preservation, staleness and response
provenance. The disposable PostgreSQL verifier upgrades through migration 0002,
round-trips a fixture observation through the real service/repository, downgrades
to base and drops only its validated temporary schema.

Local migration 0002 is applied. The first live World Bank attempt on 2026-09-20
timed out after bounded retries, recorded failed:provider_timeout and promoted no
observations. This is correct failure behavior, not live-provider verification.
Retry from an environment with confirmed outbound HTTPS before enabling a
scheduled production refresh.
