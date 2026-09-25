import cmath
import math
import os
import numpy as np

# ==========================================
# 1. FUNCIONES AUXILIARES Y DE UTILIDAD
# ==========================================

def factor_multiplicativo(lista_entrada):
    conteo_decimales = list()
    for valor in lista_entrada:
        sub_lista = valor.split('.')
        if len(sub_lista) > 1:
            cant_decimales = len(sub_lista[1])
        else:
            cant_decimales = 0
        conteo_decimales.append(cant_decimales)
    max_decimales = max(conteo_decimales) if conteo_decimales else 0
    factor = pow(10, max_decimales)
    return factor


def angulo_de_transmision(diferencia_angular):
    if diferencia_angular > 180:
        mu_raw = 360 - diferencia_angular
    else:
        mu_raw = diferencia_angular

    if mu_raw > 90:
        mu = 180 - mu_raw
    else:
        mu = mu_raw

    return mu


def generar_valores_beta_3(beta_2, diccionario_rangos):
    if beta_2 not in diccionario_rangos:
        # Si no hay configuración para ese beta_2, devolvemos vacío (salta)
        return []

    config = diccionario_rangos[beta_2]
    paso = config['Paso']
    valores_beta_3 = []

    if paso == 0:
        # paso inválido
        return []

    for subint in config['Subintervalos']:
        lim_inf = subint['Limite inferior']
        lim_sup = subint['Limite superior']
        lim_parada = lim_sup + 1 if paso > 0 else lim_sup - 1
        for val in range(lim_inf, lim_parada, paso):
            valores_beta_3.append(val)

    return valores_beta_3

# === AGREGADO: FILTRO DE RAMA (NUEVA FUNCIÓN AUXILIAR) ===
def evaluar_defecto_rama(V_rect, U_rect, alfa2_deg, alfa3_deg, beta2_der_deg, beta3_der_deg):
    """
    Evalúa si el mecanismo de 4 barras presenta defecto de rama (branch defect) entre las 3 posiciones.
    Determina el signo de la orientación (producto cruz entre el vector acoplador V y la manivela/balancín U)
    en las posiciones 1, 2 y 3.
    Retorna True si todas las posiciones pertenecen a la misma rama (válido), False si cambia de rama.
    """
    # Posición 1
    V1 = V_rect
    U1 = U_rect

    # Posición 2
    V2 = V1 * cmath.exp(1j * math.radians(alfa2_deg))
    U2 = U1 * cmath.exp(1j * math.radians(beta2_der_deg))

    # Posición 3
    V3 = V1 * cmath.exp(1j * math.radians(alfa3_deg))
    U3 = U1 * cmath.exp(1j * math.radians(beta3_der_deg))

    # Componente Z del producto cruz 2D (V_x * U_y - V_y * U_x) que define la rama
    cross1 = V1.real * U1.imag - V1.imag * U1.real
    cross2 = V2.real * U2.imag - V2.imag * U2.real
    cross3 = V3.real * U3.imag - V3.imag * U3.real

    signo1 = np.sign(cross1)
    signo2 = np.sign(cross2)
    signo3 = np.sign(cross3)

    # Si alguna posición cae en singularidad/punto muerto (cross == 0), se descarta
    if signo1 == 0 or signo2 == 0 or signo3 == 0:
        return False

    # Valida que las 3 posiciones conserven el mismo signo de orientación
    return (signo1 == signo2 == signo3)
# ========================================================


# === AGREGADO: FILTRO POR BETA_3 (NUEVA FUNCIÓN AUXILIAR) ===
def filtro_beta3_valido(beta3_izq_deg, beta3_der_deg, limite=100):
    """
    Evalúa el filtro de descarte por beta_3: si el beta_3 de la diada izquierda Y el beta_3
    de la diada derecha son ambos mayores a 'limite' en valor absoluto, el mecanismo se descarta.
    Retorna True si el mecanismo debe conservarse, False si debe descartarse.
    """
    return not (abs(beta3_izq_deg) > limite and abs(beta3_der_deg) > limite)
# ==============================================================


# ==========================================
# 2. FUNCIONES DE CÁLCULO CIENTÍFICO Y MATRICIAL
# ==========================================

def regla_de_cramer(valores_prescritos, matrices_creadas):
    tamano = len(valores_prescritos)
    matriz_A = np.array(valores_prescritos[0:tamano - 1]).transpose()
    matrices_creadas.append(matriz_A)
    for i in range(tamano - 1):
        matriz_copia = matriz_A.copy()
        matriz_copia[:, i] = valores_prescritos[tamano - 1]
        matrices_creadas.append(matriz_copia)

    valores_determinantes = list()
    for matriz in matrices_creadas:
        valores_determinantes.append(np.linalg.det(matriz))

    valor_incognitas = list()
    for i in range(1, len(valores_determinantes)):
        if valores_determinantes[0] == 0:
            print("\n[!] Error: El determinante principal es cero. El sistema no tiene solución única.")
            break
        div = valores_determinantes[i] / valores_determinantes[0]
        # cmath.polar(div) devuelve (magnitud, fase en radianes)
        valor_incognitas.append(cmath.polar(div))

    return valor_incognitas


def resolver_mecanismo(opciones_libres, datos_prescritos):
    """
    opciones_libres: [[beta2_izq_deg, beta3_izq_deg], [beta2_der_deg, beta3_der_deg]]
    datos_prescritos: [[alfa2_deg, alfa3_deg], [delta2_complex, delta3_complex]]
    ---
    IMPORTANTE: Los delta se usan tal cual (forma rectangular: complex),
    sin pasar por exp(1j*delta)-1. Los beta y alfa siguen transformándose con exp(1j*rad)-1.
    """
    lados = ['izquierda', 'derecha']
    iteraciones = len(lados)
    resultados = list()

    for i in range(iteraciones):
        valores_prescritos = [opciones_libres[i]] + datos_prescritos
        valores_x_lados = list()

        # Procesar beta y alfa (convertir de grados a radianes y aplicar e^(i*rad) - 1)
        for elementos in valores_prescritos[:-1]:
            lista_temporal = list()
            for numero in elementos:
                rad = math.radians(float(numero))
                dato_formateado = cmath.exp(1j * rad) - 1
                lista_temporal.append(dato_formateado)
            valores_x_lados.append(lista_temporal)

        # Procesar delta: AHORA usamos la forma rectangular tal cual (complex),
        # NO aplicamos exp(1j*delta)-1 aquí.
        # Asumimos que valores_prescritos[-1] ya contiene objetos complex.
        deltas_rectangulares = []
        for delta in valores_prescritos[-1]:
            # Si por alguna razón delta viene como string (ej. "3+2j"), convertimos a complex
            if isinstance(delta, str):
                delta_complex = complex(delta.replace(" ", "").replace("*", ""))
            else:
                delta_complex = complex(delta)
            # Usamos directamente la representación rectangular (no exponencial)
            deltas_rectangulares.append(delta_complex)
        valores_x_lados.append(deltas_rectangulares)

        matrices_creadas = list()
        valor_incognitas = regla_de_cramer(valores_x_lados, matrices_creadas)
        resultados.append(valor_incognitas)

    return resultados


# ==========================================
# 3. FUNCIONES DE INTERFAZ, LECTURA Y ALMACENAMIENTO
# ==========================================

def datos_prescritos(cant_incognitas):
    datos_prescritos = list()

    print(f"\n============================================\n   INGRESANDO DATOS PRESCRITOS \n============================================")

    # 1. Validación para 'alfa'
    alfas = list()
    print("\n--- Ingreso de Ángulos Alfa (en grados) ---")
    for i in range(cant_incognitas):
        while True:
            try:
                entrada = input(f"  • Introduzca alfa {i + 2}: ")
                valor = float(entrada)
                alfas.append(valor)
                break
            except ValueError:
                print("  [!] Error: Ingrese un valor numérico válido (ej. 30 o 45.5).")
    datos_prescritos.append(alfas)

    # 2. Validación para 'delta' (los transformamos a complex aquí)
    deltas = list()
    print("\n--- Ingreso de Desplazamientos Delta (en forma a+bj) ---")
    for i in range(cant_incognitas):
        while True:
            try:
                entrada = input(f"  • Introduzca delta {i + 2} (ej. 3+2j o 5-1j): ").replace(" ", "").replace("*", "")
                valor = complex(entrada)   # ahora guardamos como complex (rectangular)
                deltas.append(valor)
                break
            except ValueError:
                print("  [!] Error: Formato no válido. Ejemplo de formato correcto: 2+3j, -1.5+4j o 3j.")
    datos_prescritos.append(deltas)

    return datos_prescritos


def guardar_mecanismo(nombre_archivo, datos):
    # === AGREGADO: ORDENAR POR MEJOR ÁNGULO DE TRANSMISIÓN ===
    # Cada fila trae 4 ángulos (ya acotados a [0°,90°] por angulo_de_transmision, donde
    # más cerca de 90° = mejor): fila[12]=mu1_izq, fila[13]=mu3_izq, fila[14]=mu1_der, fila[15]=mu3_der.
    # Para cada lado se toma el peor de sus dos posiciones extremas (min), y entre los
    # dos lados se toma el mejor disponible (max), ya que basta con que un lado sirva
    # para manejar el mecanismo. Se ordena de mayor a menor ese valor.
    datos = sorted(
        datos,
        key=lambda fila: max(min(fila[12], fila[13]), min(fila[14], fila[15])),
        reverse=True
    )
    # ===========================================================
    # Encabezados agrupados con formato visual amplio
    linea_sup = f"{'DIADA IZQUIERDA':^60}{'DIADA DERECHA':^60}{'MANIVELA IZQ':^20}{'MANIVELA DER':^20}\n"

    sub_encabezados = (
        f"{'β_2 (°)':>10}{'β_3 (°)':>10}{'w (mm)':>10}{'θ_w (°)':>10}{'z (mm)':>10}{'θ_z (°)':>10}"
        f"{'β_2 (°)':>10}{'β_3 (°)':>10}{'w (mm)':>10}{'θ_w (°)':>10}{'z (mm)':>10}{'θ_z (°)':>10}"
        f"{'μ_1 (°)':>10}{'μ_3 (°)':>10}{'μ_1 (°)':>10}{'μ_3 (°)':>10}\n"
    )

    separador = "═" * 160 + "\n"
    linea_fina = "─" * 160 + "\n"

    with open(nombre_archivo, "w", encoding="utf-8") as archivo:
        archivo.write(separador)
        archivo.write(linea_sup)
        archivo.write(linea_fina)
        archivo.write(sub_encabezados)
        archivo.write(separador)

        for fila in datos:
            # Convertir los ángulos que están en radianes a grados antes de imprimir.
            # Estructura esperada de 'fila' (índices, 0-based):
            # 0: beta2_izq (deg)
            # 1: beta3_izq (deg)
            # 2: w_izq (magnitud)
            # 3: theta_w_izq (radianes)  <-- convertir a grados
            # 4: z_izq (magnitud)
            # 5: theta_z_izq (radianes)  <-- convertir a grados
            # 6: beta2_der (deg)
            # 7: beta3_der (deg)
            # 8: w_der (magnitud)
            # 9: theta_w_der (radianes)  <-- convertir a grados
            #10: z_der (magnitud)
            #11: theta_z_der (radianes)  <-- convertir a grados
            #12..: angulos de transmision (ya en grados)

            fila_convertida = []
            for idx, dato in enumerate(fila):
                if idx in (3, 5, 9, 11):
                    # Convertir radianes -> grados antes de formatear
                    valor_en_grados = math.degrees(dato)
                    fila_convertida.append(valor_en_grados)
                else:
                    fila_convertida.append(dato)

            linea = "".join([f"{valor:>10.3f}" for valor in fila_convertida]) + "\n"
            archivo.write(linea)


# ==========================================
# 4. FLUJO PRINCIPAL DE EJECUCIÓN (MAIN)
# ==========================================

def main():

    CANT_INCOGNITAS = 2

    datos_prescritos_lista = datos_prescritos(CANT_INCOGNITAS)

    rangos_beta_2 = {}
    parametros_rango = ['Limite inferior', 'Limite superior', 'Paso']
    strings_beta_2 = list()

    print("\n--- Configuración de Rango para Beta 2 ---")
    for parametro in parametros_rango:
        while True:
            try:
                valor_ingresado = input(f"  • {parametro} de beta 2: ")
                val_float = float(valor_ingresado)

                # Validación para que el paso no sea cero
                if parametro == 'Paso' and val_float == 0:
                    print("  [!] Error: El paso no puede ser 0.")
                    continue

                strings_beta_2.append(valor_ingresado)
                valor_ingresado = val_float
                break
            except ValueError:
                print("  [!] Error: No es un valor numérico válido. Intente de nuevo.")
        rangos_beta_2[parametro] = valor_ingresado

    factor_beta_2 = factor_multiplicativo(strings_beta_2)

    for parametro in rangos_beta_2:
        rangos_beta_2[parametro] = round(rangos_beta_2[parametro] * factor_beta_2)

    # Se ajusta la tupla de Beta 2 sumando el paso al límite superior para incluirlo
    paso_b2 = rangos_beta_2['Paso']
    rango_beta_2 = (
        rangos_beta_2['Limite inferior'],
        rangos_beta_2['Limite superior'] + (1 if paso_b2 > 0 else -1),
        paso_b2
    )

    rangos_beta_3_x_beta_2 = {}
    strings_beta_3 = list()

    print("\n--- Configuración de Rango para Beta 3 ---")
    for beta_2 in range(*rango_beta_2):
        beta_2_real = beta_2 / factor_beta_2
        print(f"\n Configuración para Beta 2 = {beta_2_real}:")

        while True:
            try:
                cant_intervalos = int(input(f"  • Cantidad de subintervalos para Beta 3: "))
                if cant_intervalos > 0:
                    break
                print("  [!] Ingrese un número entero mayor a 0.")
            except ValueError:
                print("  [!] Error: Debe ingresar un número entero.")

        subintervalos = []
        for i in range(cant_intervalos):
            print(f"    Subintervalo {i + 1}:")
            limites = {}
            for lim in ['Limite inferior', 'Limite superior']:
                while True:
                    try:
                        val_str = input(f"      - {lim}: ")
                        float(val_str)
                        strings_beta_3.append(val_str)
                        limites[lim] = float(val_str)
                        break
                    except ValueError:
                        print("      [!] Error: No es un valor numérico válido.")

            subintervalos.append(limites)

        while True:
            try:
                paso_str = input(f"  • Paso para Beta 3: ")
                paso_val = float(paso_str)

                if paso_val == 0:
                    print("  [!] Error: El paso debe ser diferente de 0.")
                    continue

                strings_beta_3.append(paso_str)
                break
            except ValueError:
                print("  [!] Error: Debe ingresar un número válido.")

        rangos_beta_3_x_beta_2[beta_2] = {'Paso': paso_val, 'Subintervalos': subintervalos}

    factor_beta_3 = factor_multiplicativo(strings_beta_3)

    # Escalar valores de Beta 3
    for beta_2 in rangos_beta_3_x_beta_2:
        rangos_beta_3_x_beta_2[beta_2]['Paso'] = round(rangos_beta_3_x_beta_2[beta_2]['Paso'] * factor_beta_3)

        for subint in rangos_beta_3_x_beta_2[beta_2]['Subintervalos']:
            subint['Limite inferior'] = round(subint['Limite inferior'] * factor_beta_3)
            subint['Limite superior'] = round(subint['Limite superior'] * factor_beta_3)

    datos = list()

    # Iteraciones del mecanismo
    for beta_2_izq in range(*rango_beta_2):
        lista_beta_3_izq = generar_valores_beta_3(beta_2_izq, rangos_beta_3_x_beta_2)

        for beta_3_izq in lista_beta_3_izq:
            lado_izquierdo = [(beta_2_izq / factor_beta_2), (beta_3_izq / factor_beta_3)]

            for beta_2_der in range(*rango_beta_2):
                lista_beta_3_der = generar_valores_beta_3(beta_2_der, rangos_beta_3_x_beta_2)

                for beta_3_der in lista_beta_3_der:
                    lado_derecho = [(beta_2_der / factor_beta_2), (beta_3_der / factor_beta_3)]

                    # === AGREGADO: FILTRO POR BETA_3 (DESCARTE TEMPRANO, ANTES DE RESOLVER LA DIADA) ===
                    if not filtro_beta3_valido(lado_izquierdo[1], lado_derecho[1]):
                        continue  # Se descarta si beta_3 izq y beta_3 der superan 100° en valor absoluto
                    # =====================================================================================

                    opciones_libres = [lado_izquierdo, lado_derecho]
                    resultados = resolver_mecanismo(opciones_libres, datos_prescritos_lista)

                    # Obtener vectores del acoplador
                    vectores_acoplador_nombres = ['Z', 'S']
                    vectores_acoplador = dict()
                    for i, lados in enumerate(resultados):
                        vectores_acoplador[vectores_acoplador_nombres[i]] = cmath.rect(lados[1][0], lados[1][1])

                    acoplador = vectores_acoplador["Z"] - vectores_acoplador["S"]

                    # Obtener vectores de la díada
                    vectores_diada_nombres = ['W', 'U']
                    vectores = dict()
                    for i, lados in enumerate(resultados):
                        vectores[vectores_diada_nombres[i]] = lados[0]
                    vectores['V'] = cmath.polar(acoplador)


                    # === AGREGADO: APLICACIÓN DEL FILTRO DE RAMA EN EL BUCLE DE SÍNTESIS ===
                    U_rect = cmath.rect(resultados[1][0][0], resultados[1][0][1])
                    alfa2_deg = datos_prescritos_lista[0][0]
                    alfa3_deg = datos_prescritos_lista[0][1]
                    beta2_der_real = beta_2_der / factor_beta_2
                    beta3_der_real = beta_3_der / factor_beta_3

                    if not evaluar_defecto_rama(acoplador, U_rect, alfa2_deg, alfa3_deg, beta2_der_real, beta3_der_real):
                        continue  # Se descarta el mecanismo si presenta defecto de rama
                    # =======================================================================

                    valores_prescritos = opciones_libres + datos_prescritos_lista

                    angulos_transmision = list()
                    tamano = len(valores_prescritos)

                    for i, nombre in enumerate(reversed(vectores_diada_nombres)):
                        # Posición 1
                        diferencia_angular = math.fabs(math.degrees(vectores[nombre][1]) - math.degrees(vectores['V'][1]))
                        mu = angulo_de_transmision(diferencia_angular)
                        angulos_transmision.append(mu)

                        # Posición 3
                        diferencia_angular = math.fabs(
                            math.degrees(vectores[nombre][1]) + float(valores_prescritos[tamano - 3 - i][1]) -
                            (math.degrees(vectores['V'][1]) + float(valores_prescritos[2][1]))
                        )
                        mu = angulo_de_transmision(diferencia_angular)
                        angulos_transmision.append(mu)

                    datos_fila = list()
                    for lista, lado in zip(resultados, opciones_libres):
                        datos_fila += lado
                        for i in range(len(lista)):
                            datos_fila += [*lista[i]]

                    datos_fila += angulos_transmision
                    datos.append(datos_fila)

    guardar_mecanismo("mecanismos_sintetizados.txt", datos)
    print("\n[✓] Cálculo completado exitosamente y datos guardados en 'mecanismos_sintetizados.txt'.")


# ==========================================
# FUNCION DE PRUEBA RÁPIDA (run_test)
# ==========================================
def run_test():
    """
    Ejecuta una síntesis puntual con los datos de control que me diste,
    sin interacción. Imprime una fila CSV comparable con las versiones previas.
    """
    # Datos de control proporcionados
    beta_2_izq = -11.4
    beta_3_izq = -96.0
    beta_2_der = -11.6
    beta_3_der = -88.0

    alpha2 = 2.0
    alpha3 = 20.0
    # Aquí los deltas en forma rectangular (complex)
    delta2 = 0.16221483 + 0.83457915j
    delta3 = 4.48839208 + 3.85019818j

    opciones_libres = [[beta_2_izq, beta_3_izq], [beta_2_der, beta_3_der]]
    datos_prescritos = [[alpha2, alpha3], [delta2, delta3]]

    resultados = resolver_mecanismo(opciones_libres, datos_prescritos)

    # Reconstruir la fila CSV (mismo orden que guardar_mecanismo/CSV simple)
    fila = []
    # izquierda: beta2, beta3
    fila += [beta_2_izq, beta_3_izq]
    # w y theta_w (del lado izquierdo) -> vienen de resultados[0][0] = (mag, phase)
    fila += [resultados[0][0][0], math.degrees(resultados[0][0][1])]
    # z y theta_z (del lado izquierdo) -> resultados[0][1]
    fila += [resultados[0][1][0], math.degrees(resultados[0][1][1])]
    # derecha
    fila += [beta_2_der, beta_3_der]
    fila += [resultados[1][0][0], math.degrees(resultados[1][0][1])]
    fila += [resultados[1][1][0], math.degrees(resultados[1][1][1])]

    # Calcular V (acoplador) para ángulos de transmisión
    Z = cmath.rect(resultados[0][1][0], resultados[0][1][1])
    S = cmath.rect(resultados[1][1][0], resultados[1][1][1])
    acoplador = Z - S
    V = cmath.polar(acoplador)
    V_ang_deg = math.degrees(V[1])

    # === AGREGADO: EVALUACIÓN DE RAMA EN PRUEBA RÁPIDA ===
    U_rect = cmath.rect(resultados[1][0][0], resultados[1][0][1])
    pasa_rama = evaluar_defecto_rama(acoplador, U_rect, alpha2, alpha3, beta_2_der, beta_3_der)
    print(f"[Filtro de Rama] ¿El mecanismo está libre de defecto de rama?: {pasa_rama}")
    # ====================================================

    # === AGREGADO: EVALUACIÓN DE FILTRO BETA_3 EN PRUEBA RÁPIDA ===
    pasa_beta3 = filtro_beta3_valido(beta_3_izq, beta_3_der)
    print(f"[Filtro Beta_3] ¿El mecanismo pasa el filtro de beta_3 (no ambos >100° abs)?: {pasa_beta3}")
    # ================================================================

    # vectores para mu: W = resultados[0][0], U = resultados[1][0]
    vectores = {'W': resultados[0][0], 'U': resultados[1][0], 'V': V}
    valores_prescritos_full = opciones_libres + datos_prescritos
    tamano = len(valores_prescritos_full)

    angulos_transmision = []
    nombre_vector = ['W', 'U']
    for i, nombre in enumerate(reversed(nombre_vector)):
        diferencia_angular = abs(math.degrees(vectores[nombre][1]) - V_ang_deg)
        mu = angulo_de_transmision(diferencia_angular)
        angulos_transmision.append(mu)
        diferencia_angular = abs(math.degrees(vectores[nombre][1]) + float(valores_prescritos_full[tamano - 3 - i][1]) - (V_ang_deg + float(valores_prescritos_full[2][1])))
        mu = angulo_de_transmision(diferencia_angular)
        angulos_transmision.append(mu)

    fila += angulos_transmision

    # Imprimir en formato CSV (3 decimales)
    header = "beta2_izq_deg,beta3_izq_deg,w_izq_mm,theta_w_izq_deg,z_izq_mm,theta_z_izq_deg,beta2_der_deg,beta3_der_deg,w_der_mm,theta_w_der_deg,z_der_mm,theta_z_der_deg,mu1_izq_deg,mu3_izq_deg,mu1_der_deg,mu3_der_deg"
    fila_3dec = [f"{x:.3f}" for x in fila]
    print(header)
    print(",".join(fila_3dec))
    # También devuelvo la fila (útil si lo quieres capturar desde Python)
    return fila

# ===========================
# EJECUCIÓN OPCIONAL:
# ===========================
if __name__ == "__main__":
    main()   # descomenta para ejecución interactiva completa
    # Para prueba rápida sin interacción, ejecuta run_test()
    # run_test()