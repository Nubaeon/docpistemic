# Docpistemic - Epistemic Documentation Coverage
# Build: docker build -t nubaeon/docpistemic:0.1.0 .
# Run:   docker run --rm nubaeon/docpistemic:0.1.0 assess https://github.com/user/repo

FROM python:3.11-alpine

LABEL maintainer="Docpistemic Team"
LABEL description="Epistemic documentation coverage assessment"
LABEL version="0.1.0"

# Install git for cloning repos
RUN apk add --no-cache git

# Upgrade pip and install docpistemic
RUN pip install --upgrade pip && \
    pip install --no-cache-dir docpistemic

# Create non-root user
RUN adduser -D -u 1000 docpistemic
USER docpistemic

WORKDIR /project

ENTRYPOINT ["docpistemic"]
CMD ["--help"]

# Usage examples:
# docker run --rm nubaeon/docpistemic assess https://github.com/fastapi/fastapi
# docker run --rm -v $(pwd):/project nubaeon/docpistemic assess /project
# docker run --rm nubaeon/docpistemic assess https://github.com/user/repo --depth 3
