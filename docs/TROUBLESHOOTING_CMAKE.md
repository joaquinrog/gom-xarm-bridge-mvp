# Solución de Problemas — Compilación (catkin_make)

## Error: `Invoking "cmake" failed` — xarm_msgs no encontrado

### Síntoma

Al ejecutar `catkin_make` en el paso 3.3 (Compilación), aparece:

```
CMake Error at /opt/ros/noetic/share/catkin/cmake/catkinConfig.cmake:83 (find_package):
  Could not find a package configuration file provided by "xarm_msgs" with
  any of the following names:

    xarm_msgsConfig.cmake
    xarm_msgs-config.cmake

-- Could NOT find xarm_msgs (missing: xarm_msgs_DIR)
Invoking "cmake" failed
```

### Causa

Cuando se usan **symlinks** para vincular `repo/xarm_ros` en `src/`, catkin a veces no actualiza su caché interno correctamente. Intenta compilar `gom_xarm_bridge` antes de que `xarm_msgs` esté disponible en el espacio de desarrollo.

### Solución

Realiza un **clean build más agresivo**:

```bash
cd ~/xArm-cobot

# 1. Limpia directorios de build (incluyendo install)
rm -rf build devel install

# 2. Asegúrate de que ROS Noetic está sourceado
source /opt/ros/noetic/setup.bash

# 3. Compila solo xarm_msgs primero (valida que está accesible)
catkin_make --only-pkg-with-deps xarm_msgs

# 4. Si el paso 3 funciona, compila todo
catkin_make
```

**Si el paso 3 aún falla**, los submódulos de `xarm_ros` no se bajaron completamente:

```bash
cd ~/xArm-cobot/repo/xarm_ros
git submodule update --init --recursive
cd ~/xArm-cobot
rm -rf build devel install
catkin_make
```

### Verificación

Después de que `catkin_make` termine (debe mostrar `[100%] Built target ...`), verifica:

```bash
source devel/setup.bash

# Estos comandos deben funcionar sin errores:
rospack find gom_xarm_bridge
rospack find xarm_msgs
python3 -c "import rospy, xarm_msgs; print('Imports OK')"
```

---

**Nota:** Es normal que la primera compilación tarde 3–8 minutos. Las compilaciones posteriores son más rápidas.
