FROM python:3.10-slim

WORKDIR /app

#system installations 

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    ffmpeg \
    python3-dbus \
    libdbus-1-dev \
    libglib2.0-dev \
    libgirepository1.0-dev \
    libcairo2-dev \
    python3-gi \
    python3-gi-cairo \
    gir1.2-gstreamer-1.0 \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    pkg-config \
    findutils \
    && rm -rf /var/lib/apt/lists/*


# hailo installation

COPY interface/backend/*.deb ./

RUN apt-get update && \
    apt-get install -y ./*.deb || echo "Erreur installation .deb ignorée pour debug" && \
    rm ./*.deb


RUN TARGET_DIR=$(python3 -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])') && \
    find /usr/lib -type d -name "hailo" -exec cp -r {} "$TARGET_DIR/" \; && \
    find /usr/lib -type d -name "hailo_sdk" -exec cp -r {} "$TARGET_DIR/" \; && \
    find /usr/lib -type d -name "hailort" -exec cp -r {} "$TARGET_DIR/" \; && \
    find /usr/lib -name "gsthailo*" -exec cp -r {} "$TARGET_DIR/" \;

# python bindings
RUN TARGET_DIR=$(python3 -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])') && \
    for pattern in /usr/lib/python3/dist-packages/hailo* /usr/lib/python3/dist-packages/gsthailo*; do \
        if [ -e "$pattern" ]; then \
            cp -r "$pattern" "$TARGET_DIR/"; \
        fi; \
    done

#installations for python wheels
RUN pip install --upgrade pip setuptools wheel && \
    pip install "PyGObject==3.48.2"
-
COPY interface/backend/venv/src/hailo-apps/scripts/hailo_python_installation.sh /tmp/hailo_python_installation.sh
RUN chmod +x /tmp/hailo_python_installation.sh && \
    /tmp/hailo_python_installation.sh --hw-arch=hailo8 --hailort-version=4.23.0 --tappas-core-version=5.1.0

COPY models/speech_to_text/requirements_stt.txt .
COPY interface/backend/requirements_backend.txt .
COPY interface/backend/requirements_cv_docker.txt .
COPY monitoring/requirements.txt requirements_monitoring.txt

RUN pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
    pip install -r requirements_stt.txt && \
    sed -i '/hailo-tappas-core/d' requirements_cv_docker.txt && \
    sed -i '/hailort/d' requirements_cv_docker.txt && \
    pip install -r requirements_cv_docker.txt && \
    pip install -r requirements_backend.txt && \
    pip install -r requirements_monitoring.txt

# reinstalling librairies for whisper compatibility
RUN pip install --force-reinstall "transformers==4.37.2" "tokenizers==0.15.1"

#post process compilation
RUN mkdir -p /usr/local/hailo/resources/so/

RUN echo "search and compilation" && \
    CPP_FILE=$(find /usr /opt -name "yolo_hailortpp_postprocess.cpp" | head -n 1) && \
    if [ -z "$CPP_FILE" ]; then \
        echo "c++ file not found, trying fallback method"; \
        find /usr /opt -name "libyolo*.so" -exec cp {} /usr/local/hailo/resources/so/libyolo_hailortpp_postprocess.so \; ; \
    else \
        echo "source found : $CPP_FILE - beginning compilation"; \
        g++ -O3 -fPIC -shared -std=c++11 "$CPP_FILE" \
            -o /usr/local/hailo/resources/so/libyolo_hailortpp_postprocess.so \
            -I/usr/include/hailo -I/usr/local/include/hailo; \
        echo "compilation successfull"; \
    fi

COPY models/ /app/models
COPY monitoring/ /app/monitoring
COPY ./interface/backend /app/interface/backend

RUN echo '{}' > /app/current_monitoring_data.json

# Paths to GObject and GStreamer
ENV GI_TYPELIB_PATH="/usr/lib/aarch64-linux-gnu/girepository-1.0:/usr/lib/girepository-1.0:/usr/local/lib/girepository-1.0"
ENV GST_PLUGIN_PATH="/usr/lib/aarch64-linux-gnu/gstreamer-1.0:/usr/lib/gstreamer-1.0:/usr/local/lib/gstreamer-1.0"
# Python Path
ENV PYTHONPATH="$PYTHONPATH:/usr/lib/aarch64-linux-gnu/hailo/tappas/core/python"
# Library Path so that ctypes can find libgsthailometa.so
ENV LD_LIBRARY_PATH="/usr/lib/aarch64-linux-gnu:/usr/lib:/usr/local/lib"

CMD ["uvicorn", "interface.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
