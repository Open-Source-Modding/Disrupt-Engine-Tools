using GeoAPI.CoordinateSystems;
using GeoAPI.CoordinateSystems.Transformations;
using GeoAPI.Geometries;
using NetTopologySuite.Geometries;
using ProjNet.CoordinateSystems;
using ProjNet.CoordinateSystems.Transformations;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Media.Media3D;

namespace Arada.classes
{
    // https://spatialreference.org

    public class ItemShapes
    {
        /// <summary>
        /// Gets a 2D Poly version of the points
        /// </summary>
        /// <returns></returns>
        public static Polygon GetPolygon(Point3D[] coordinates)
        {
            var coords = new Coordinate[coordinates.Count() + 1];
            for (int i = 0; i < coordinates.Count(); i++)
            {
                coords[i] = new Coordinate(coordinates[i].X, coordinates[i].Y);
            }
            coords[coordinates.Count()] = coords[0];
            GeometryFactory factory = new GeometryFactory(new PrecisionModel(), 0); //4326
            return (Polygon)factory.CreatePolygon(new LinearRing(coords));
        }
        public static Objects.Json.Polygon GetJsonPoly(IGeometry b, string type, string name, string id)
        {
            var f = new Objects.Json.Polygon();

            f.type = "Feature";
            f.properties.name = name;
            f.properties.id = id;
            f.geometry.type = "Polygon";
            f.properties.type = type;
            f.geometry.coordinates = Objects.Json.ObjFunctions.MakePolygon(b);

            return f;
        }
        public static Double? GetArea3D(Objects.Geometries.ObjVector3F[] positions)
        {
            if(positions == null)
            { return null; }
            else if (positions.Length != 3)
            { return null; }

            GeometryFactory factory = new GeometryFactory(new PrecisionModel(), 0); //4326  SRID declaration
            Coordinate[] coordsTri = new Coordinate[]{
                new Coordinate((double)positions[0].X,(double)positions[0].Y,(double)positions[0].Z),
                new Coordinate((double)positions[1].X,(double)positions[1].Y,(double)positions[1].Z),
                new Coordinate((double)positions[2].X,(double)positions[2].Y,(double)positions[2].Z)
			};
            var result = Triangle.Area3D(coordsTri[0], coordsTri[1], coordsTri[2]);
            if (Double.IsNaN(result) || result == 0)
            {
                var test2d = Triangle.Area(coordsTri[0], coordsTri[1], coordsTri[2]);
                // var test3d = Area3D(coordsTri[0], coordsTri[1], coordsTri[2]);
            }
            return result;
        }
        public static double Area3D(Coordinate a, Coordinate b, Coordinate c)
        {
            /*
             * Uses the formula 1/2 * | u x v |
             * where
             * 	u,v are the side vectors of the triangle
             *  x is the vector cross-product
             */
            // side vectors u and v
            double ux = b.X - a.X;
            double uy = b.Y - a.Y;
            double uz = b.Z - a.Z;

            double vx = c.X - a.X;
            double vy = c.Y - a.Y;
            double vz = c.Z - a.Z;

            // cross-product = u x v 
            double crossx = uy * vz - uz * vy;
            double crossy = uz * vx - ux * vz;
            double crossz = ux * vy - uy * vx;

            // tri area = 1/2 * | u x v |
            double absSq = crossx * crossx + crossy * crossy + crossz * crossz;
            double area3D = Math.Sqrt(absSq) / 2;

            return area3D;
        }

        /// <summary>
        /// https://gis.stackexchange.com/questions/165022/how-do-i-transform-a-point-using-nettopologysuite
        /// </summary>
        public static void TestConversion()
        {
            ICoordinateTransformation WebMercatorToWgs84 =
            (new CoordinateTransformationFactory())
            .CreateFromCoordinateSystems(ProjectedCoordinateSystem.WebMercator, GeographicCoordinateSystem.WGS84);
        }
        public void TestTransformListOfCoordinates()
        {
 

            CoordinateSystemFactory csFact = new CoordinateSystemFactory();
            CoordinateTransformationFactory ctFact = new CoordinateTransformationFactory();
            
            ICoordinateSystem utm35ETRS = csFact.CreateFromWkt(
                    "PROJCS[\"ETRS89 / ETRS-TM35\",GEOGCS[\"ETRS89\",DATUM[\"D_ETRS_1989\",SPHEROID[\"GRS_1980\",6378137,298.257222101]],PRIMEM[\"Greenwich\",0],UNIT[\"Degree\",0.017453292519943295]],PROJECTION[\"Transverse_Mercator\"],PARAMETER[\"latitude_of_origin\",0],PARAMETER[\"central_meridian\",27],PARAMETER[\"scale_factor\",0.9996],PARAMETER[\"false_easting\",500000],PARAMETER[\"false_northing\",0],UNIT[\"Meter\",1]]");
                    
            IProjectedCoordinateSystem utm33 = ProjectedCoordinateSystem.WGS84_UTM(33, true);

            ICoordinateTransformation trans = ctFact.CreateFromCoordinateSystems(utm35ETRS, utm33);

            Coordinate[] points = new Coordinate[]
            {
            new Coordinate(290586.087, 6714000), new Coordinate(290586.392, 6713996.224),
            new Coordinate(290590.133, 6713973.772), new Coordinate(290594.111, 6713957.416),
            new Coordinate(290596.615, 6713943.567), new Coordinate(290596.701, 6713939.485)
            };

            Coordinate[] tpoints = trans.MathTransform.TransformList(points).ToArray();
            /*
            for (int i = 0; i < points.Length; i++)
                Assert.That(tpoints[i].Equals(trans.MathTransform.Transform(points[i])));
            */
        }

        /// <summary>
        /// Assumes source is engine coordinates.
        /// </summary>
        /// <param name="points"></param>
        /// <returns></returns>
        public Point3D[] ConvertToWgs84(Point3D[] s)
        {
            float scaleFactor = Settings.settings.geographyWebMercatorScaleFactor;

            var coordArray = new Coordinate[s.Count()];
            for (int i = 0; i < s.Count(); i++)
            {
                coordArray[i] = new Coordinate(s[i].X * scaleFactor, s[i].Y * scaleFactor, s[i].Z * scaleFactor);
            }
            var convertedCoord = ConvertToWgs84(coordArray);
            var points = new Point3D[s.Count()];
            for (int i = 0; i < s.Count(); i++)
            {
                points[i] = new Point3D(convertedCoord[i].X, convertedCoord[i].Y, convertedCoord[i].Z);
            }

            return points;
        }

        public Coordinate[] ConvertToWgs84(Coordinate[] points)
        {
            // test 3114

            NetTopologySuite.Geometries.PrecisionModel precisionModel = new NetTopologySuite.Geometries.PrecisionModel(GeoAPI.Geometries.PrecisionModels.Floating);

            CoordinateSystem wgs84 = GeographicCoordinateSystem.WGS84 as CoordinateSystem;
            CoordinateSystem mercatore = ProjectedCoordinateSystem.WebMercator as CoordinateSystem;
            ICoordinateSystemFactory cFac = new CoordinateSystemFactory();

            int SRID_wgs84 = System.Convert.ToInt32(wgs84.AuthorityCode);    //WGS84 SRID
            int SRID_mercatore = System.Convert.ToInt32(mercatore.AuthorityCode); //Mercatore SRID

            ProjNet.CoordinateSystems.Transformations.CoordinateTransformationFactory ctFact = new ProjNet.CoordinateSystems.Transformations.CoordinateTransformationFactory();
            GeoAPI.CoordinateSystems.Transformations.ICoordinateTransformation transformation = ctFact.CreateFromCoordinateSystems(mercatore, wgs84);
            
            return transformation.MathTransform.TransformList(points).ToArray();

        }

        /// <summary>
        /// https://csharp.hotexamples.com/examples/-/ProjNet.CoordinateSystems.Transformations.CoordinateTransformationFactory/CreateFromCoordinateSystems/php-projnet.coordinatesystems.transformations.coordinatetransformationfactory-createfromcoordinatesystems-method-examples.html
        /// </summary>
        public void TestConvertToWgs84()
        {
            NetTopologySuite.Geometries.PrecisionModel precisionModel = new NetTopologySuite.Geometries.PrecisionModel(GeoAPI.Geometries.PrecisionModels.Floating);

            CoordinateSystem wgs84 = GeographicCoordinateSystem.WGS84 as CoordinateSystem;
            CoordinateSystem mercatore = ProjectedCoordinateSystem.WebMercator as CoordinateSystem;
            ICoordinateSystemFactory cFac = new CoordinateSystemFactory();

            int SRID_wgs84 = System.Convert.ToInt32(wgs84.AuthorityCode);    //WGS84 SRID
            int SRID_mercatore = System.Convert.ToInt32(mercatore.AuthorityCode); //Mercatore SRID

            ProjNet.CoordinateSystems.Transformations.CoordinateTransformationFactory ctFact = new ProjNet.CoordinateSystems.Transformations.CoordinateTransformationFactory();
            GeoAPI.CoordinateSystems.Transformations.ICoordinateTransformation transformation = ctFact.CreateFromCoordinateSystems(mercatore, wgs84);

            //6378137
            Coordinate[] points = new Coordinate[]
            {
            new Coordinate(290586.087, 6714000), new Coordinate(290586.392, 6713996.224),
            new Coordinate(290590.133, 6713973.772), new Coordinate(290594.111, 6713957.416),
            new Coordinate(290596.615, 6713943.567), new Coordinate(290596.701, 6713939.485)
            }; 

            Coordinate[] tpoints = transformation.MathTransform.TransformList(points).ToArray();
            
        }
    }
}
