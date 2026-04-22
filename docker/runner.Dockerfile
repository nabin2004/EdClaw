# Minimal runner image for DockerSandbox (extend with compilers as needed)
FROM debian:bookworm-slim
RUN useradd -u 65534 -r -s /usr/sbin/nologin nobody || true
WORKDIR /work
USER nobody
CMD ["sleep", "infinity"]
