# syntax=docker/dockerfile:1
FROM mcr.microsoft.com/dotnet/sdk:9.0@sha256:ca77338a19f87a7d24494a3656cb7d878a040c158621337b9cd3ab811c5eb057 AS build
WORKDIR /src

COPY Challenge/Challenge.csproj Challenge/
RUN dotnet restore Challenge/Challenge.csproj

COPY Challenge/ Challenge/
RUN dotnet publish Challenge/Challenge.csproj -o /app/out

FROM mcr.microsoft.com/dotnet/runtime:9.0@sha256:1ba87a6c8246f80d6fde1e83fa0bc277200879cfdd5d68df5e40933255ac1ff3 AS runtime
WORKDIR /app
COPY --from=build /app/out ./
ENTRYPOINT ["dotnet", "Challenge.dll"]
