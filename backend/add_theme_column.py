from sqlalchemy import text
from app.core.database import engine

def add_theme_column():
    """Agregar columna theme_id a la tabla landing_pages"""
    try:
        with engine.connect() as conn:
            # Verificar si la columna ya existe
            result = conn.execute(text("PRAGMA table_info(landing_pages)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'theme_id' not in columns:
                conn.execute(text('ALTER TABLE landing_pages ADD COLUMN theme_id INTEGER'))
                conn.commit()
                print('Columna theme_id agregada exitosamente')
            else:
                print('La columna theme_id ya existe')
                
    except Exception as e:
        print(f'Error al agregar columna: {e}')

if __name__ == '__main__':
    add_theme_column()