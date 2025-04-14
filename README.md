# Integrasi Sistem 2025 - gRPC: Inventory Management

## Kelompok

| Name                    | NRP        |
|-------------------------|------------|
| Amoes Noland            | 5027231028 |
| Dionisius Marcell Putra Indranto | 5027231044 |
| Tio Axellino Irin | 5027231065 |

## Usage

### Prerequisite

* Have Python and the tools required to run.
```sh
pip install grpcio grpcio-tools flask
```

### Compiling Proto
```sh
python -m grpc_tools.protoc --proto_path=. --python_out=. --grpc_python_out=. inventory.proto
```

### Starting

#### Server:
```sh
python inventory_server.py
```

#### Client:
```sh
python app.py
```