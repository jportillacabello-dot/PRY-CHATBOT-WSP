#!/bin/bash
set -e

echo "=== Inicialización del harness ==="

if [ -f package.json ]; then
  if [ -f pnpm-lock.yaml ]; then
    PM="pnpm"
  elif [ -f yarn.lock ]; then
    PM="yarn"
  elif [ -f bun.lock ] || [ -f bun.lockb ]; then
    PM="bun"
  else
    PM="npm"
  fi

  echo "=== Instalando dependencias con $PM ==="
  if [ "$PM" = "npm" ]; then
    npm install
  else
    "$PM" install
  fi

  node -e "const s=require('./package.json').scripts||{}; process.exit(s.check||s.typecheck||s['type-check']?0:1)" && {
    if node -e "const s=require('./package.json').scripts||{}; process.exit(s.check?0:1)"; then
      [ "$PM" = "npm" ] && npm run check || "$PM" run check
    elif node -e "const s=require('./package.json').scripts||{}; process.exit(s.typecheck?0:1)"; then
      [ "$PM" = "npm" ] && npm run typecheck || "$PM" run typecheck
    else
      [ "$PM" = "npm" ] && npm run type-check || "$PM" run type-check
    fi
  }

  node -e "const s=require('./package.json').scripts||{}; process.exit(s.lint?0:1)" && {
    [ "$PM" = "npm" ] && npm run lint || "$PM" run lint
  }

  node -e "const s=require('./package.json').scripts||{}; process.exit(s.test?0:1)" && {
    [ "$PM" = "npm" ] && npm test || "$PM" test
  }

  node -e "const s=require('./package.json').scripts||{}; process.exit(s.build?0:1)" && {
    [ "$PM" = "npm" ] && npm run build || "$PM" run build
  }
elif [ -f pyproject.toml ] || [ -f requirements.txt ]; then
  echo "=== Verificación de Python ==="
  PY="$(command -v python3 || command -v python)"
  # pytest sale con código 5 si no encuentra tests: no es un fallo en un proyecto nuevo.
  "$PY" -m pytest || [ $? -eq 5 ]
  # -x omite entornos virtuales y carpetas de build para no compilar dependencias.
  "$PY" -m compileall -q -x '(^|/)(\.?venv|env|node_modules|build|dist|__pycache__)(/|$)' .
elif [ -f go.mod ]; then
  echo "=== Verificación de Go ==="
  go test ./...
elif [ -f Cargo.toml ]; then
  echo "=== Verificación de Rust ==="
  cargo test
elif [ -f pom.xml ]; then
  echo "=== Verificación de Maven ==="
  mvn test
elif [ -f build.gradle ] || [ -f build.gradle.kts ]; then
  echo "=== Verificación de Gradle ==="
  ./gradlew test
elif ls *.csproj *.sln >/dev/null 2>&1; then
  echo "=== Verificación de .NET ==="
  dotnet test
else
  echo "No se detectó ningún manifiesto de paquetes conocido."
  echo "Reemplaza esta sección por los comandos de verificación del proyecto."
fi

echo "=== Verificación completa ==="
echo ""
echo "Próximos pasos (Next steps):"
echo "1. Lee feature_list.json para ver el estado actual de las funcionalidades"
echo "2. Elige UNA funcionalidad sin terminar"
echo "3. Implementa solo esa funcionalidad"
echo "4. Vuelve a verificar antes de decir que está terminada"
