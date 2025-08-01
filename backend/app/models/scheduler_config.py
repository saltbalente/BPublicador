from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import json

from app.core.database import Base

class SchedulerConfig(Base):
    __tablename__ = "scheduler_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # Configuración básica
    enabled = Column(Boolean, default=False)
    interval = Column(String(50), default="daily")  # 5min, 15min, 30min, hourly, daily, twice_daily, weekly
    max_posts_per_day = Column(Integer, default=5)
    
    # Configuración de contenido
    auto_publish = Column(Boolean, default=False)
    generate_images = Column(Boolean, default=True)
    content_style = Column(String(100), default="professional")
    word_count_min = Column(Integer, default=500)
    word_count_max = Column(Integer, default=1500)
    
    # Configuración de horarios
    schedule_time = Column(String(10), nullable=True)  # HH:MM format
    days_of_week = Column(Text, nullable=True)  # JSON array of days
    
    # Estado del scheduler
    status = Column(String(50), default="not_configured")  # not_configured, configured, active, paused, error
    is_running = Column(Boolean, default=False)
    
    # Timestamps de ejecución
    last_execution = Column(DateTime, nullable=True)
    next_execution = Column(DateTime, nullable=True)
    
    # Metadatos
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Configuración adicional como JSON
    additional_config = Column(Text, nullable=True)  # JSON string for extra settings
    
    # Relación con usuario
    user = relationship("User", back_populates="scheduler_config")
    
    def to_dict(self):
        """Convertir a diccionario"""
        config = {
            "id": self.id,
            "user_id": self.user_id,
            "enabled": self.enabled,
            "interval": self.interval,
            "max_posts_per_day": self.max_posts_per_day,
            "auto_publish": self.auto_publish,
            "generate_images": self.generate_images,
            "content_style": self.content_style,
            "word_count_min": self.word_count_min,
            "word_count_max": self.word_count_max,
            "schedule_time": self.schedule_time,
            "status": self.status,
            "is_running": self.is_running,
            "last_execution": self.last_execution.isoformat() if self.last_execution else None,
            "next_execution": self.next_execution.isoformat() if self.next_execution else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        
        # Agregar días de la semana si existen
        if self.days_of_week:
            try:
                config["days_of_week"] = json.loads(self.days_of_week)
            except:
                config["days_of_week"] = []
        
        # Agregar configuración adicional si existe
        if self.additional_config:
            try:
                additional = json.loads(self.additional_config)
                config.update(additional)
            except:
                pass
        
        return config
    
    def update_from_dict(self, config_dict):
        """Actualizar desde diccionario"""
        # Campos básicos
        if "enabled" in config_dict:
            self.enabled = config_dict["enabled"]
        if "interval" in config_dict:
            self.interval = config_dict["interval"]
        if "max_posts_per_day" in config_dict:
            self.max_posts_per_day = config_dict["max_posts_per_day"]
        if "auto_publish" in config_dict:
            self.auto_publish = config_dict["auto_publish"]
        if "generate_images" in config_dict:
            self.generate_images = config_dict["generate_images"]
        if "content_style" in config_dict:
            self.content_style = config_dict["content_style"]
        if "word_count_min" in config_dict:
            self.word_count_min = config_dict["word_count_min"]
        if "word_count_max" in config_dict:
            self.word_count_max = config_dict["word_count_max"]
        if "schedule_time" in config_dict:
            self.schedule_time = config_dict["schedule_time"]
        if "status" in config_dict:
            self.status = config_dict["status"]
        if "is_running" in config_dict:
            self.is_running = config_dict["is_running"]
        
        # Días de la semana
        if "days_of_week" in config_dict:
            self.days_of_week = json.dumps(config_dict["days_of_week"])
        
        # Configuración adicional
        additional_fields = {}
        for key, value in config_dict.items():
            if key not in [
                "enabled", "interval", "max_posts_per_day", "auto_publish", 
                "generate_images", "content_style", "word_count_min", 
                "word_count_max", "schedule_time", "status", "is_running", 
                "days_of_week", "user_id", "id", "created_at", "updated_at",
                "last_execution", "next_execution"
            ]:
                additional_fields[key] = value
        
        if additional_fields:
            self.additional_config = json.dumps(additional_fields)
        
        self.updated_at = datetime.utcnow()