Small services stay easiest to maintain with one thin `main`, and everything else under `internal/`.

```
myservice/
├── go.mod
├── cmd/server/main.go        (wiring only)
└── internal/
    ├── config/               (env -> Config struct)
    ├── server/               (routes + middleware)
    ├── handler/              (HTTP <-> domain)
    └── store/                (DB / persistence)

Dependency flow (arrows point at what is imported):

┌─────────────────┐
│  cmd/server     │  main.go: load config, build deps, run
└────────┬────────┘
         │ builds
         ▼
┌─────────────────┐     ┌─────────────────┐
│ internal/config │     │ internal/server │  mux, middleware
└─────────────────┘     └────────┬────────┘
                                 │ routes to
                                 ▼
                        ┌─────────────────┐
                        │ internal/handler│  decode, call store, encode
                        └────────┬────────┘
                                 │ uses (via interface)
                                 ▼
                        ┌─────────────────┐
                        │ internal/store  │  Postgres, in-memory, etc.
                        └─────────────────┘
```

Key ideas: `main` only wires things together, handlers depend on a small interface that `store` satisfies (easy to fake in tests), and shutdown is graceful.

```go
// cmd/server/main.go
package main

import (
	"context"
	"errors"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"example.com/myservice/internal/config"
	"example.com/myservice/internal/server"
	"example.com/myservice/internal/store"
)

func main() {
	if err := run(); err != nil {
		slog.Error("fatal", "err", err)
		os.Exit(1)
	}
}

func run() error {
	cfg, err := config.FromEnv()
	if err != nil {
		return err
	}

	logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))
	st := store.NewMemory() // swap for store.NewPostgres(cfg.DatabaseURL)

	srv := &http.Server{
		Addr:              cfg.Addr,
		Handler:           server.New(logger, st),
		ReadHeaderTimeout: 5 * time.Second,
		ReadTimeout:       10 * time.Second,
		WriteTimeout:      15 * time.Second,
		IdleTimeout:       60 * time.Second,
	}

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	errCh := make(chan error, 1)
	go func() {
		logger.Info("listening", "addr", cfg.Addr)
		if err := srv.ListenAndServe(); !errors.Is(err, http.ErrServerClosed) {
			errCh <- err
		}
	}()

	select {
	case err := <-errCh:
		return err
	case <-ctx.Done():
		logger.Info("shutting down")
	}

	shutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	return srv.Shutdown(shutdownCtx)
}
```

And the routing in `internal/server`, using Go 1.22+ method-aware patterns so you don't need a router library:

```go
// internal/server/server.go
func New(logger *slog.Logger, st handler.Store) http.Handler {
	h := handler.New(logger, st)

	mux := http.NewServeMux()
	mux.HandleFunc("GET /healthz", h.Health)
	mux.HandleFunc("GET /items/{id}", h.GetItem)
	mux.HandleFunc("POST /items", h.CreateItem)

	return logging(logger)(mux) // wrap middleware here
}
```

Start with the standard library and add dependencies (chi, sqlc, etc.) only when a real need appears. I can scaffold this in the working directory if you'd like.
