using NetTopologySuite.Geometries;
using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Media.Media3D;

namespace Arada.classes
{
    public class ItemDebugAnnotationShape
    {
        public static Geometry GetGeometry(LayerContentObject obj)
        {
            GeometryFactory factory = new GeometryFactory(new PrecisionModel(), 0); //4326  SRID declaration

            var coords = GetCoordinates(obj);
            var geo = classes.ItemShapes.GetPolygon(coords);
            var metadata = new Objects.ObjDebugAnnotationShape(obj);
            geo.UserData = metadata;
            return geo;

        }
        public static Point3D[] GetCoordinates(LayerContentObject obj)
        {
            // var rotatedPoint = classes.Matrix.GetPoint(new float[3] { 1f, 1f, 0 }, 30);
            /*
              <Object Type="Building" 
              Id="{1292B407-47EF-43A1-991B-0D3BFD11D3E1}" 
              Name="Building_1913551" 
              Pos="1160.68,82.0184,104.972" 
              Angles="0,0,51.5872" 
              WorldPos="1160.68,82.0184,104.972">
             
            <Corner vecCornerPos="-3.99994,-8,0" />
			<Corner vecCornerPos="-4.00006,4,0" />
			<Corner vecCornerPos="1.99994,3.99982,0" />
			<Corner vecCornerPos="2.00006,-8.00018,0" />
              */
            Point3D[] coords = new Point3D[obj.Points.Length + 1]; // Poly must be closed, so +1

            var objLoc = new Objects.ObjLocation(obj.WorldPos, obj.Angles);
            for (int i = 0; i < obj.Points.Length; i++)
            {
                var cornerCoord = classes.Matrix.ConvertStringCoordToFloat(obj.Points[i].Pos);
                //rotate & place in worldspace
                if (objLoc.rotation != null)
                {
                    cornerCoord = classes.Matrix.RotatePoint(cornerCoord, objLoc.rotation[2]); //objLoc.location
                }
                if (objLoc.location != null)
                {
                    cornerCoord.X += objLoc.location[0];
                    cornerCoord.Y += objLoc.location[1];
                    cornerCoord.Z += objLoc.location[2];
                    coords[i] = new Point3D(cornerCoord.X, cornerCoord.Y, cornerCoord.Z);
                }
            }
            coords[obj.Points.Length] = coords[0];

            return coords;
        }

        public static string GenerateJson(ConcurrentBag<GeoAPI.Geometries.IGeometry> bagGeo)
        {
            var bagPolys = new ConcurrentBag<Objects.Json.Polygon>();


            var geo = new Objects.Json.GeoJson();
                foreach (var b in bagGeo)
                {
                    var metadata = (Objects.ObjDebugAnnotationShape)b.UserData;
                    var shape = ItemShapes.GetJsonPoly(b, metadata.Type, metadata.Name, metadata.Id);
                    geo.features.Add(shape);
                }

            // GeoJson
            return Objects.Json.ObjFunctions.GenerateJsonFile(geo);

        }

    }
}
