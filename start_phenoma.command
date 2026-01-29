echo "========================================"
echo "   Iniciando Profiling Tool de Nuevas Masculinidades Provokers"
echo "========================================"

# 1. Navegar al directorio del proyecto
cd "/Users/diegoturueno/.gemini/antigravity/scratch/provokers_masculinity"

# 2. Activar entorno de Anaconda
source /opt/anaconda3/bin/activate

# 3. Abrir el navegador automáticamente (espera 2 seg para dar tiempo al servidor)
(sleep 2 && open "http://127.0.0.1:5001") &

# 4. Iniciar el servidor Flask
echo "Servidor iniciándose..."
echo "Si necesitas detenerlo, cierra esta ventana."
python app.py
