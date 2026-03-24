
import os
import time

def generate_svg_logo(company_name, shapes="circle", primary_color="#000000"):
    """
    Generates a minimalist and geometric vector logo (SVG).
    This allows for SHARP text and perfect shapes.
    """
    
    # Plantilla básica de SVG Geométrico
    svg_content = f"""
    <svg width="500" height="500" viewBox="0 0 500 500" xmlns="http://www.w3.org/2000/svg">
        <!-- Fondo -->
        <rect width="100%" height="100%" fill="white"/>
        
        <!-- Central Graphic Element (Abstract) -->
        <g transform="translate(250, 200)">
            <circle cx="0" cy="0" r="120" fill="none" stroke="{primary_color}" stroke-width="10" />
            <path d="M-80,80 L80,-80 M-80,-80 L80,80" stroke="{primary_color}" stroke-width="15" stroke-linecap="round" />
            <rect x="-40" y="-40" width="80" height="80" fill="{primary_color}" opacity="0.8" />
        </g>
        
        <!-- Texto de la Marca (Perfecto y Legible) -->
        <text x="250" y="420" 
              font-family="'Courier New', monospace" 
              font-size="50" 
              font-weight="bold" 
              fill="black" 
              text-anchor="middle" 
              letter-spacing="5">
              {company_name.upper()}
        </text>
        
        <!-- Tagline -->
        <text x="250" y="460" 
              font-family="Arial, sans-serif" 
              font-size="18" 
              fill="#555" 
              text-anchor="middle" 
              letter-spacing="2">
              MARKETING INTELLIGENCE
        </text>
    </svg>
    """
    
    carpeta = "PROYECTOS_GENERADOS/ARTE"
    if not os.path.exists(carpeta): os.makedirs(carpeta)
    
    nombre_archivo = f"logo_vectorial_{int(time.time())}.svg"
    ruta = os.path.join(carpeta, nombre_archivo)
    
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(svg_content)
        
    return ruta

def save_svg_v3(content: str, filename_base: str):
    """
    Saves raw SVG content to the Dashboard's public folder.
    """
    folder = "dashboard/assets/generated"
    if not os.path.exists(folder): os.makedirs(folder)
    
    file_name = f"{filename_base}_{int(time.time())}.svg"
    abs_path = os.path.join(folder, file_name)
    
    # Limpieza básica
    content = content.replace("```xml", "").replace("```svg", "").replace("```", "").strip()
    
    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    # Return relative path for the frontend
    return f"assets/generated/{file_name}"
