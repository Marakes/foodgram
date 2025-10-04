# ---------- build stage ----------
FROM node:18-alpine AS build
WORKDIR /app

COPY package*.json ./
RUN npm ci --no-audit --no-fund

COPY . .

RUN npm run build

FROM alpine:3.20 AS runtime
WORKDIR /app
COPY --from=build /app/build ./build


# build env
#FROM node:21.7.1-alpine
#WORKDIR /app
#COPY package*.json ./
#RUN npm install
#COPY . ./
#RUN npm run build
#CMD cp -r build result_build
