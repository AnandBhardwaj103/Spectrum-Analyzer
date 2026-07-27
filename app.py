import cv2
import numpy as np
from scipy.interpolate import griddata
import plotly.graph_objects as go

# ==========================================
# STEP 1: Extract Data from Images (OpenCV)
# ==========================================
def extract_polar_from_image(image_path, center_xy, max_pixel_radius):
    """
    Reads a 2D plot image, isolates the colored trace, and converts it to (angle, radius).
    Assumes a colored trace (e.g., red) on a standard polar grid.
    """
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Could not find {image_path}")

    # Convert to HSV to easily isolate the trace color (assuming a red trace here)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Define color range for the trace (adjust these for your specific images)
    lower_color = np.array([0, 50, 50])
    upper_color = np.array([10, 255, 255])
    
    # Create a mask to isolate the trace
    mask = cv2.inRange(hsv, lower_color, upper_color)
    
    # Find the pixels that make up the trace
    y_coords, x_coords = np.where(mask > 0)
    
    angles = []
    radii = []
    
    # Convert every pixel on the trace to polar coordinates relative to the center
    for x, y in zip(x_coords, y_coords):
        dx = x - center_xy[0]
        dy = center_xy[1] - y  # Invert Y because image Y goes down
        
        # Calculate angle (-pi to pi) and radius (pixels)
        angle = np.arctan2(dy, dx)
        radius = np.sqrt(dx**2 + dy**2)
        
        # Normalize radius from 0.0 to 1.0 (or actual dB/linear scale)
        norm_radius = radius / max_pixel_radius
        
        angles.append(angle)
        radii.append(norm_radius)
        
    return np.array(angles), np.array(radii)

# ==========================================
# STEP 2: Map to Spherical Coordinates
# ==========================================
def map_to_spherical(xy_data, yz_data, zx_data):
    """
    Maps the 2D plane angles into a shared 3D spherical space (theta, phi, R).
    Spherical convention: 
    theta = inclination angle [0, pi] (from Z axis down)
    phi = azimuthal angle [0, 2*pi] (around Z axis, from X axis)
    """
    points = [] # Holds (theta, phi)
    values = [] # Holds R (radius/gain)
    
    # 1. XY Plane (Azimuth): theta is 90 degrees (pi/2)
    xy_angles, xy_radii = xy_data
    for ang, r in zip(xy_angles, xy_radii):
        theta = np.pi / 2
        phi = ang if ang >= 0 else ang + 2*np.pi
        points.append((theta, phi))
        values.append(r)
        
    # 2. YZ Plane (Elevation 1): phi is 90 deg (pi/2) or 270 deg (3*pi/2)
    yz_angles, yz_radii = yz_data
    for ang, r in zip(yz_angles, yz_radii):
        # Map 2D polar angle to 3D theta/phi
        phi = np.pi/2 if ang > 0 else 3*np.pi/2
        theta = np.abs(ang)
        points.append((theta, phi))
        values.append(r)

    # 3. ZX Plane (Elevation 2): phi is 0 or 180 deg (pi)
    zx_angles, zx_radii = zx_data
    for ang, r in zip(zx_angles, zx_radii):
        phi = 0 if ang > 0 else np.pi
        theta = np.abs(ang)
        points.append((theta, phi))
        values.append(r)
        
    return np.array(points), np.array(values)

# ==========================================
# STEP 3 & 4: Interpolate & Convert to Cartesian
# ==========================================
def generate_3d_surface(points, values, resolution=100):
    """
    Interpolates the missing data points to create a solid 3D envelope,
    then converts to X, Y, Z for plotting.
    """
    # Create a dense grid of theta and phi covering the whole sphere
    grid_theta, grid_phi = np.mgrid[0:np.pi:complex(resolution), 0:2*np.pi:complex(resolution)]
    
    # Use SciPy to interpolate the radius (R) for every point on our grid based on the known 2D cuts
    # 'nearest' or 'linear' works best here depending on data density
    grid_R = griddata(points, values, (grid_theta, grid_phi), method='nearest')
    
    # Step 4: Convert Spherical (R, theta, phi) back to Cartesian (X, Y, Z)
    X = grid_R * np.sin(grid_theta) * np.cos(grid_phi)
    Y = grid_R * np.sin(grid_theta) * np.sin(grid_phi)
    Z = grid_R * np.cos(grid_theta)
    
    return X, Y, Z, grid_R

# ==========================================
# STEP 5: Render with Plotly
# ==========================================
def render_3d_pattern(X, Y, Z, R_values):
    """
    Opens an interactive HTML window with the 3D surface.
    """
    fig = go.Figure(data=[go.Surface(
        x=X, y=Y, z=Z,
        surfacecolor=R_values, # Color maps to the gain/radius
        colorscale='Jet',
        opacity=0.9
    )])

    fig.update_layout(
        title="Interpolated 3D RF Radiation Pattern",
        scene=dict(
            xaxis=dict(title='X Axis'),
            yaxis=dict(title='Y Axis'),
            zaxis=dict(title='Z Axis'),
            aspectmode='data' # Keeps the sphere proportion accurate
        ),
        margin=dict(l=0, r=0, b=0, t=40)
    )
    
    fig.show()

# ==========================================
# MAIN EXECUTION & MOCK DATA GENERATOR
# ==========================================
if __name__ == "__main__":
    try:
        print("Attempting to load real images...")
        # Replace these with your actual image paths and center pixel coordinates
        xy_data = extract_polar_from_image("xy_cut.png", center_xy=(250, 250), max_pixel_radius=200)
        yz_data = extract_polar_from_image("yz_cut.png", center_xy=(250, 250), max_pixel_radius=200)
        zx_data = extract_polar_from_image("zx_cut.png", center_xy=(250, 250), max_pixel_radius=200)
        print("Images loaded successfully!")
        
    except FileNotFoundError:
        print("Images not found. Generating synthetic mock data to demonstrate the 3D pipeline...")
        # Generate a synthetic directional lobe pattern
        angles = np.linspace(-np.pi, np.pi, 360)
        
        # Fake XY (Omnidirectional base, slightly directional)
        xy_radii = 0.5 + 0.5 * np.cos(angles)
        xy_data = (angles, xy_radii)
        
        # Fake YZ (Elevation lobe)
        yz_radii = np.abs(np.cos(angles)**2)
        yz_data = (angles, yz_radii)
        
        # Fake ZX (Elevation lobe)
        zx_radii = np.abs(np.cos(angles)**2)
        zx_data = (angles, zx_radii)

    print("Mapping to spherical space...")
    points, values = map_to_spherical(xy_data, yz_data, zx_data)
    
    print("Interpolating 3D surface (this takes a moment)...")
    X, Y, Z, R_values = generate_3d_surface(points, values, resolution=150)
    
    print("Launching interactive Plotly window...")
    render_3d_pattern(X, Y, Z, R_values)
