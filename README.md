# desafio-aiqfome

## Justificativas

Para não poluir o guia de instalação e execução optei por deixar a justificava das escolhas de arquitetura dentro de um documento separado denominado "Justificativas" na pasta raiz do projeto.

## Instalação com Docker

1. **Copie o arquivo de ambiente**
   ```bash
   cp env.example .env
   ```

2. **Construa e suba os serviços**
   ```bash
   docker compose up --build
   ```

3. **Serviços expostos**
   - API: <http://localhost:8000>
   - Swagger UI: <http://localhost:8000/api/docs/>
   - Esquema OpenAPI (JSON): <http://localhost:8000/api/schema/>
   - PostgreSQL: `localhost:5438`
   - Elasticsearch: <http://localhost:9200>

---

## Envs

| Variável | Função | Padrão (Docker) |
| --- | --- | --- |
| `DJANGO_ALLOWED_HOSTS` | Hosts aceitos pelo Django | `localhost,127.0.0.1,0.0.0.0,web` |
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | Configuração do PostgreSQL | `db`, `5432`, `desafio_aiqfome`, `Gandalf`, `Mellon` |
| `ES_HOST`, `ES_PRODUCTS_INDEX` | Conexão e índice do Elasticsearch | `http://search:9200`, `products` |

Ajuste o `.env` se executar o Django fora do Docker (exemplo: `ES_HOST=http://localhost:9200`).

---

## Dados no Elasticsearch

Preencha o índice de produtos após iniciar a stack:

```bash
docker compose exec web python scripts/seed_elasticsearch.py
```

Execute novamente quando precisar renovar os dados de exemplo.

---

## Executando testes

```bash
docker compose exec web python manage.py test
```

Para desenvolvimento local sem Docker:

```bash
poetry install
poetry run python manage.py migrate
poetry run python manage.py test
```

---

## Fluxo de autenticação

Todos os endpoints protegidos exigem JWT.

1. **Crie um cliente** (sem autenticação):
   ```bash
   curl -X POST http://localhost:8000/users/ \
     -H "Content-Type: application/json" \
     -d '{"name":"Keyleth","email":"keyleth@example.com","password":"verdant123"}'
   ```

2. **Obtenha um token de acesso**:
   ```bash
   curl -X POST http://localhost:8000/api/token/ \
     -H "Content-Type: application/json" \
     -d '{"email":"keyleth@example.com","password":"verdant123"}'
   ```

   Resposta:
   ```json
   {
     "refresh": "<refresh-token>",
     "access": "<access-token>"
   }
   ```

3. **Envie o token nas requisições protegidas**:
   ```
   Authorization: Bearer <access-token>
   ```

4. **Renove o token de acesso quando expirar**:
   ```bash
   curl -X POST http://localhost:8000/api/token/refresh/ \
     -H "Content-Type: application/json" \
     -d '{"refresh":"<refresh-token>"}'
   ```

Endpoints restritos a staff (como a listagem de clientes) exigem um usuário staff autenticado. Crie-o via shell ou admin do Django.

---

## Swagger e Schema

- **Swagger UI**: <http://localhost:8000/api/docs/>  
  Possui botão “Authorize” (`Bearer <token>`).
- **OpenAPI JSON**: <http://localhost:8000/api/schema/>

---

## Referência de endpoints

### Autenticação

| Método | Rota | Descrição | Payload |
| --- | --- | --- | --- |
| `POST` | `/api/token/` | Gera tokens de acesso/refresh | `{"email": "...", "password": "..."}` |
| `POST` | `/api/token/refresh/` | Renova o token de acesso | `{"refresh": "<token>"}` |

---

### Clientes

#### `POST /users/` — Registrar cliente  
*Sem autenticação.*

```json
{
  "name": "Keyleth",
  "email": "keyleth@example.com",
  "password": "verdant123"
}
```

Exemplo:
```bash
curl -X POST http://localhost:8000/users/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Keyleth","email":"keyleth@example.com","password":"verdant123"}'
```

#### `GET /users/` — Listar clientes  
*Requer token de staff.*

```bash
curl http://localhost:8000/users/ \
  -H "Authorization: Bearer <staff-access-token>"
```

#### `GET /users/{customer_id}/` — Consultar cliente  
*Cliente ou staff autenticado.*

```bash
curl http://localhost:8000/users/1/ \
  -H "Authorization: Bearer <access-token>"
```

#### `PUT /users/{customer_id}/` — Atualizar cliente  
*Cliente ou staff autenticado.*

```json
{
  "name": "Keyleth Ashari",
  "email": "keyleth@example.com"
}
```

```bash
curl -X PUT http://localhost:8000/users/1/ \
  -H "Authorization: Bearer <access-token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Keyleth Ashari","email":"keyleth@example.com"}'
```

#### `DELETE /users/{customer_id}/` — Remover cliente  
*Cliente ou staff autenticado.*

```bash
curl -X DELETE http://localhost:8000/users/1/ \
  -H "Authorization: Bearer <access-token>"
```

---

### Favoritos

Todos os endpoints exigem o cliente autenticado correspondente ou um usuário staff.

#### `GET /users/{customer_id}/favorites/`
```bash
curl http://localhost:8000/users/1/favorites/ \
  -H "Authorization: Bearer <access-token>"
```

#### `POST /users/{customer_id}/favorites/`
```json
{
  "product_id": 42
}
```

```bash
curl -X POST http://localhost:8000/users/1/favorites/ \
  -H "Authorization: Bearer <access-token>" \
  -H "Content-Type: application/json" \
  -d '{"product_id":42}'
```

#### `DELETE /users/{customer_id}/favorites/{product_id}/`
```bash
curl -X DELETE http://localhost:8000/users/1/favorites/42/ \
  -H "Authorization: Bearer <access-token>"
```

---

### Busca no catálogo (Elasticsearch)

`GET /products/search/` — Sem autenticação. Filtros opcionais:

| Parâmetro | Descrição |
| --- | --- |
| `keyword` | Termo para título/descrição |
| `min_price`, `max_price` | Faixa de preço |
| `min_rating` | Nota mínima |

Exemplo:
```bash
curl "http://localhost:8000/products/search/?keyword=robe&min_price=100&max_price=600&min_rating=4"
```

---

## Comandos úteis

- Shell do Django no container:
  ```bash
  docker compose exec web python manage.py shell
  ```
- Criar usuário staff:
  ```bash
  docker compose exec web python manage.py createsuperuser
  ```
- Acompanhar logs:
  ```bash
  docker compose logs -f web
  ```
- Alternativamente aos comandos apresentados neste documeto, é possível utilizar os comandos do Makefile.
