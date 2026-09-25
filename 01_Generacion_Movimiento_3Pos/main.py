import sys
# Importamos la lógica pura desde tu otro archivo dentro de la misma carpeta
from kinematic_sweep_3pos import ejecutar_barrido, guardar_resultados, run_test

def solicitar_datos_consola():
    """Captura los parámetros prescritos y rangos de barrido desde la terminal."""
    print("\n--- 1. INGRESAR ÁNGULOS Y DESPLAZAMIENTOS PRESCRITOS ---")
    alpha2 = float(input("Ángulo alpha 2 (°): "))
    alpha3 = float(input("Ángulo alpha 3 (°): "))
    
    delta2_x = float(input("Desplazamiento delta 2 en X (mm): "))
    delta2_y = float(input("Desplazamiento delta 2 en Y (mm): "))
    delta3_x = float(input("Desplazamiento delta 3 en X (mm): "))
    delta3_y = float(input("Desplazamiento delta 3 en Y (mm): "))
    
    # Convertimos los desplazamientos a forma compleja (X + jY)
    delta2 = complex(delta2_x, delta2_y)
    delta3 = complex(delta3_x, delta3_y)

    print("\n--- 2. CONFIGURAR BARRIDO PARAMÉTRICO (GRID SEARCH) ---")
    beta_min = float(input("Ángulo beta inicial (°): "))
    beta_max = float(input("Ángulo beta final (°): "))
    paso = float(input("Paso de incremento (°): "))

    config_barrido = {
        'beta_min': beta_min,
        'beta_max': beta_max,
        'paso': paso
    }
    
    return alpha2, alpha3, delta2, delta3, config_barrido

def main():
    """Función principal que orquesta la ejecución."""
    while True:
        print("\n==============================================")
        print("   SUITE DE SÍNTESIS DE MECANISMOS (3 POS)   ")
        print("==============================================")
        print("1. Ejecutar barrido con datos manuales")
        print("2. Ejecutar prueba rápida (Test con datos predeterminados)")
        print("3. Salir")
        
        opcion = input("\nSeleccione una opción (1-3): ").strip()

        if opcion == "1":
            alpha2, alpha3, delta2, delta3, config = solicitar_datos_consola()
            print("\nProcesando barrido, aplicando filtro de rama y ordenando por transmisión...")
            
            # Llamada al algoritmo que tú programaste
            mecanismos = ejecutar_barrido(alpha2, alpha3, delta2, delta3, config)
            
            if mecanismos:
                guardar_resultados(mecanismos, "mecanismos_sintetizados.txt")
                print(f"\n[ÉXITO] Se encontraron {len(mecanismos)} mecanismos válidos.")
                print("Resultados ordenados y guardados en 'mecanismos_sintetizados.txt'.")
            else:
                print("\n[AVISO] No se encontraron mecanismos válidos con esos rangos.")

        elif opcion == "2":
            run_test()

        elif opcion == "3":
            print("\nSaliendo de la aplicación.")
            sys.exit()
            
        else:
            print("\n[ERROR] Opción no válida. Intente de nuevo.")

if __name__ == "__main__":
    main()