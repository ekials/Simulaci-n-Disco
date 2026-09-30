from bisect import bisect_left

MAX_CLAVES = 4


class NodoT:
    def __init__(self, claves=None, registros=None):
        self.claves    = claves if claves is not None else []
        self.registros = registros if registros is not None else []
        self.izq       = None
        self.der       = None
        self.altura    = 1

    @property
    def min(self):
        return self.claves[0] if self.claves else None

    @property
    def max(self):
        return self.claves[-1] if self.claves else None


def _altura(nodo):
    return nodo.altura if nodo else 0

def _actualizar_altura(nodo):
    nodo.altura = 1 + max(_altura(nodo.izq), _altura(nodo.der))

def _balance(nodo):
    return _altura(nodo.izq) - _altura(nodo.der) if nodo else 0

def _rotar_der(y):
    x     = y.izq
    T     = x.der
    x.der = y
    y.izq = T
    _actualizar_altura(y)
    _actualizar_altura(x)
    return x

def _rotar_izq(x):
    y     = x.der
    T     = y.izq
    y.izq = x
    x.der = T
    _actualizar_altura(x)
    _actualizar_altura(y)
    return y

def _rebalancear(nodo):
    _actualizar_altura(nodo)
    b = _balance(nodo)
    if b > 1:
        if _balance(nodo.izq) < 0:
            nodo.izq = _rotar_izq(nodo.izq)
        return _rotar_der(nodo)
    if b < -1:
        if _balance(nodo.der) > 0:
            nodo.der = _rotar_der(nodo.der)
        return _rotar_izq(nodo)
    return nodo


def _insertar_entrada(nodo, clave, regs):
    if nodo is None:
        return NodoT([clave], [regs])

    if clave < nodo.min and nodo.izq is not None:
        nodo.izq = _insertar_entrada(nodo.izq, clave, regs)
    elif clave > nodo.max and nodo.der is not None:
        nodo.der = _insertar_entrada(nodo.der, clave, regs)
    else:
        i = bisect_left(nodo.claves, clave)
        if i < len(nodo.claves) and nodo.claves[i] == clave:
            nodo.registros[i].extend(regs)
            return nodo

        if len(nodo.claves) >= MAX_CLAVES:
            if i == 0:
                ck = nodo.claves.pop()
                rg = nodo.registros.pop()
                nodo.claves.insert(0, clave)
                nodo.registros.insert(0, regs)
                nodo.der = _insertar_entrada(nodo.der, ck, rg)
            else:
                nodo.claves.insert(i, clave)
                nodo.registros.insert(i, regs)
                ck = nodo.claves.pop(0)
                rg = nodo.registros.pop(0)
                nodo.izq = _insertar_entrada(nodo.izq, ck, rg)
        else:
            nodo.claves.insert(i, clave)
            nodo.registros.insert(i, regs)

    return _rebalancear(nodo)

def insertar(nodo, clave, offset, plato):
    return _insertar_entrada(nodo, clave, [(offset, plato)])


def construir_desde_ordenado(items):
    bloques = [items[i:i + MAX_CLAVES] for i in range(0, len(items), MAX_CLAVES)]

    def build(lo, hi):
        if lo > hi:
            return None
        mid  = (lo + hi) // 2
        blq  = bloques[mid]
        nodo = NodoT([c for c, _ in blq], [r for _, r in blq])
        nodo.izq = build(lo, mid - 1)
        nodo.der = build(mid + 1, hi)
        _actualizar_altura(nodo)
        return nodo

    return build(0, len(bloques) - 1)


def buscar(nodo, clave):
    while nodo is not None:
        if clave < nodo.min:
            nodo = nodo.izq
        elif clave > nodo.max:
            nodo = nodo.der
        else:
            i = bisect_left(nodo.claves, clave)
            if i < len(nodo.claves) and nodo.claves[i] == clave:
                return nodo.registros[i]
            return None
    return None

def buscar_rango(nodo, clave_min, clave_max, resultados=None):
    if resultados is None:
        resultados = []
    if nodo is None:
        return resultados
    if clave_min < nodo.min:
        buscar_rango(nodo.izq, clave_min, clave_max, resultados)
    for c, regs in zip(nodo.claves, nodo.registros):
        if clave_min <= c <= clave_max:
            resultados.extend(regs)
    if clave_max > nodo.max:
        buscar_rango(nodo.der, clave_min, clave_max, resultados)
    return resultados


def construir_indice(registros_raw, estructura, campo):
    idx_campo = next(
        (i for i, c in enumerate(estructura) if c['nombre'] == campo),
        None
    )
    if idx_campo is None:
        raise ValueError(f"campo '{campo}' no existe en la estructura")
    tipo = estructura[idx_campo]['tipo']

    grupos = {}
    for offset, registro in registros_raw:
        valor_raw = registro[idx_campo]
        if valor_raw is None:
            continue
        if tipo == 'int':
            clave = int(valor_raw)
        elif tipo in ('float', 'double'):
            clave = float(valor_raw)
        else:
            clave = str(valor_raw).lower()
        grupos.setdefault(clave, []).append((offset, 0))

    items = sorted(grupos.items(), key=lambda kv: kv[0])
    return construir_desde_ordenado(items)