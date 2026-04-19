FROM golang:1.24-alpine

RUN apk add --no-cache ffmpeg

WORKDIR /app

COPY go.mod go.sum* ./
RUN go mod download

COPY . .

RUN go build -o main ./cmd/SpeechCloak

EXPOSE 8080

CMD ["./main"]