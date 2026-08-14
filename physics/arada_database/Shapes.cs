using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using GeoAPI.CoordinateSystems;
using GeoAPI.CoordinateSystems.Transformations;
using GeoAPI.Geometries;
using NetTopologySuite.Geometries;
using NetTopologySuite.Index.Strtree;
using NetTopologySuite.IO;

namespace Arada.classes.Testing
{
    /// <summary>
    /// https://github.com/NetTopologySuite/NetTopologySuite
    /// http://nts.sourceforge.net/?page=Examples
    /// https://gis.stackexchange.com/questions/165022/how-do-i-transform-a-point-using-nettopologysuite
    /// 
    /// </summary>
    /// 
    //
    // cos 60° = Adjacent / Hypotenuse 
    // https://www.mathsisfun.com/algebra/trig-finding-side-right-triangle.html

    public class Shapes
    {
        // https://github.com/NetTopologySuite/NetTopologySuite/blob/develop/NetTopologySuite.Samples.Console/Geometries/basicexample.cs
        // https://gist.github.com/kiichi/c44dd9f65b954ade7d1f
        // https://dev.mysql.com/doc/refman/8.0/en/spatial-type-overview.html
        public void Test2()
        {
            // The SRS denoted in MySQL by SRID 0 represents an infinite flat Cartesian plane with no units assigned to its axes
            GeometryFactory factory = new GeometryFactory(new PrecisionModel(), 0); //4326  SRID declaration

            // Edge of Central Park
            Point p1 = (Point)factory.CreatePoint(new Coordinate(-73.957986, 40.800566));
            Point p2 = (Point)factory.CreatePoint(new Coordinate(-73.949575, 40.797187));
            double dist = p1.Distance(p2);
            Console.WriteLine("Edge (West-East) of Central Park: " + dist);

            // Around Central Park
            Coordinate[] coords = new Coordinate[]{
                new Coordinate(-73.957986,40.800566),
                new Coordinate(-73.949575,40.797187),
                new Coordinate(-73.972921,40.764951),
                new Coordinate(-73.981676,40.768071),
                new Coordinate(-73.957986,40.800566) // Close this polygon!
			};
            LineString lineStr = (LineString)factory.CreateLineString(coords);
            double marginDist = lineStr.Length;
            Console.WriteLine("Margin Distance of Central Park: " + marginDist);

            Polygon poly = (Polygon)factory.CreatePolygon(new LinearRing(coords));
            Console.WriteLine("Central Park Area: " + poly.Area);

            // 
            Coordinate[] coords2 = new Coordinate[]{
                new Coordinate(-71.957986,39.800566),
                new Coordinate(-76.949575,40.797187),
                new Coordinate(-75.972921,40.764951),
                new Coordinate(-74.981676,40.768071),
                new Coordinate(-71.957986,39.800566) // Close this polygon!
			};
            Polygon poly2 = (Polygon)factory.CreatePolygon(new LinearRing(coords2));
            var test1 = poly.Touches(poly2);
            var test2 = poly2.Touches(poly);
            var test3 = poly.Overlaps(poly2);
            var test4 = poly2.Overlaps(poly);
            var test5 = poly.Intersects(poly2);
            var test6 = poly2.Intersects(poly);
            var test7 = poly.Intersection(poly2);
            var test8 = poly2.Intersection(poly);

            Coordinate[] coords3= new Coordinate[]{
                new Coordinate(-10,0),
                new Coordinate(0,0),
                new Coordinate(0,10),
                new Coordinate(-10,10),
                new Coordinate(-10,0) // Close this polygon!
			};
            Coordinate[] coords4 = new Coordinate[]{
                new Coordinate(-20,0),
                new Coordinate(0,0),
                new Coordinate(0,20),
                new Coordinate(-20,20),
                new Coordinate(-20,0) // Close this polygon!
			};
            Polygon poly3 = (Polygon)factory.CreatePolygon(new LinearRing(coords3));
            Polygon poly4 = (Polygon)factory.CreatePolygon(new LinearRing(coords4));

            Coordinate[] coords5 = new Coordinate[]{
                new Coordinate(-20,0),
                new Coordinate(3.5,0),
                new Coordinate(0,21.225),
                new Coordinate(-20,21.55),
                new Coordinate(-20,0) // Close this polygon!
			};
            Polygon poly5 = (Polygon)factory.CreatePolygon(new LinearRing(coords5));

            Coordinate[] coordsSmall = new Coordinate[]{
                new Coordinate(-2,1),
                new Coordinate(0,1),
                new Coordinate(0,2),
                new Coordinate(-2,2),
                new Coordinate(-2,1) // Close this polygon!
			};
            Polygon polySmall = (Polygon)factory.CreatePolygon(new LinearRing(coordsSmall));

            Point loc = (Point)factory.CreatePoint(new Coordinate(-1.5, 0));

            //Transform testing

            var offset = classes.ItemWlu.GetOffsetFromCameraYaw(Settings.settings.wluLoadingOffset, 2.67); // length infront of camera to sample, rotation in world ( YAW )
            Coordinate[] coordsOffset = new Coordinate[polySmall.Coordinates.Count()];
            //Transform testing
            Console.WriteLine("ORIG:");
            for (int i = 0; i < polySmall.Coordinates.Count(); i++)
            {
                Console.WriteLine(polySmall.Coordinates[i]);
                coordsOffset[i] = new Coordinate(polySmall.Coordinates[i].X + offset[0], polySmall.Coordinates[i].Y + offset[1], polySmall.Coordinates[i].Z);
            }
            polySmall = (Polygon)factory.CreatePolygon(new LinearRing(coordsOffset));
            Console.WriteLine("UPDATED:");
            for (int i = 0; i < polySmall.Coordinates.Count(); i++)
            {
                Console.WriteLine(polySmall.Coordinates[i]);
            }





            Point loc2 = (Point)factory.CreatePoint(new Coordinate(-10.5, 10));
            var centroid = poly4.Centroid;
            //poly4.

            var testb1 = poly3.Touches(poly4);
            var testb2 = poly4.Touches(poly3);
            var testb3 = poly3.Overlaps(poly4);
            var testb4 = poly4.Overlaps(poly3);
            var testb5 = poly3.Intersects(poly4); // works
            var testb6 = poly4.Intersects(poly3); // works
            var testb7 = poly3.Intersection(poly4);
            var testb8 = poly4.Intersection(poly3);
            var testb9 = poly3.Intersection(poly5);
            var testb10 = poly4.Intersection(poly5);

            var testb11 = poly3.Intersects(poly5); // works
            var testb12 = poly4.Intersects(poly5); // works
            var testb13 = poly3.Intersects(polySmall); // works
            var testb14 = poly4.Intersects(polySmall); // works
            var testb15 = polySmall.Intersects(poly3); // works
            var testb16 = polySmall.Intersects(poly4); // works

            var testc = polySmall.Touches(loc);
            var testc2 = polySmall.Intersects(loc);

            var testc3 = polySmall.IsWithinDistance(loc, 10f); // works
            var testc4 = polySmall.IsWithinDistance(loc2, 5f); // works
            var testc5 = polySmall.IsWithinDistance(loc2, 25f); // works

            int waitforResults = 1;

        }
       
        
        public void CheckPointAgainstGeometry( )
        {
            GeometryFactory factory = new GeometryFactory(new PrecisionModel(), 0); //4326  SRID declaration

            Coordinate[] coordsSmall = new Coordinate[]{
                new Coordinate(-2,1),
                new Coordinate(0,1),
                new Coordinate(0,2),
                new Coordinate(-2,2),
                new Coordinate(-2,1) // Close this polygon!
			};
            Coordinate[] coordsSmall2 = new Coordinate[]{
                new Coordinate(-3,1),
                new Coordinate(0,1),
                new Coordinate(0,4),
                new Coordinate(-2,3),
                new Coordinate(-3,1) // Close this polygon!
			};
            Coordinate[] coordsSmall3 = new Coordinate[]{
                new Coordinate(2,1),
                new Coordinate(3,1),
                new Coordinate(3,2),
                new Coordinate(2,2),
                new Coordinate(2,1) // Close this polygon!
			};
            Polygon polySmall = (Polygon)factory.CreatePolygon(new LinearRing(coordsSmall));
            Polygon polySmall2 = (Polygon)factory.CreatePolygon(new LinearRing(coordsSmall2));
            Polygon polySmall3 = (Polygon)factory.CreatePolygon(new LinearRing(coordsSmall3));

            List<IGeometry> shapes = new List<IGeometry>();
            shapes.Add(polySmall);
            shapes.Add(polySmall2);
            shapes.Add(polySmall3);
            Point loc = (Point)factory.CreatePoint(new Coordinate(-1.5, 1.2));

            CheckPointAgainstGeometry(shapes, loc);

        }

        public void Test3dGeometry()
        {
            GeometryFactory factory = new GeometryFactory(new PrecisionModel(), 0); //4326  SRID declaration
            Coordinate[] coordsTri = new Coordinate[]{
                new Coordinate(0,2,1),
                new Coordinate(-2,2,-20),
                new Coordinate(-2,1,1) // Close this polygon!
			};
            Coordinate[] coordsSmallBent = new Coordinate[]{
                new Coordinate(-2,1,1),
                new Coordinate(0,1,1),
                new Coordinate(0,2,1),
                new Coordinate(-2,2,-20),
                new Coordinate(-2,1,1) // Close this polygon!
			};
            Coordinate[] coordsSmall = new Coordinate[]{
                new Coordinate(-2,1,1),
                new Coordinate(0,1,1),
                new Coordinate(0,2,1),
                new Coordinate(-2,2,1),
                new Coordinate(-2,1,1) // Close this polygon!
			};
            var lr = new LineString(coordsSmallBent);
            var lrA = lr.Area;
            Polygon polySmallBent = (Polygon)factory.CreatePolygon(new LinearRing(coordsSmallBent));
            Polygon polySmall = (Polygon)factory.CreatePolygon(new LinearRing(coordsSmall));
            Geometry g = (Geometry)factory.CreateGeometry(polySmallBent);
            Geometry g2 = (Geometry)factory.CreateGeometry(polySmall);
            var t = NetTopologySuite.Triangulate.DelaunayTriangulationBuilder.Envelope(coordsSmallBent);
            var t2 = NetTopologySuite.Triangulate.DelaunayTriangulationBuilder.ExtractUniqueCoordinates(g2);
            var areaTest = Triangle.Area3D(coordsTri[0], coordsTri[1], coordsTri[2]);
            var loopLength = Math.Ceiling((decimal)((coordsSmallBent.Length -1) / 3));
            for (int i = 0; i < loopLength; i++)
            {

            }


            var areaBent = polySmallBent.Area;
            var area = polySmall.Area;
            var ag = g.Area;
            bool t22 = true;
        }



        public void CheckPointAgainstGeometry(List<IGeometry> shapes, IPoint point)
        {
            // https://gis.stackexchange.com/questions/238786/how-do-i-obtain-the-shape-at-a-specific-coordinate-using-nts

            // fast way of checking intersections.


            // List<IGeometry> shapes = ...;
            // IPoint point = ...;

            // Builds the index
            STRtree<IGeometry> index = new STRtree<IGeometry>();
            foreach (IGeometry shape in shapes)
                index.Insert(shape.EnvelopeInternal, shape);
            index.Build();

            // Makes the query. The 'nearShapes' are the shapes whose envelopes contains the point.
            IList<IGeometry> nearShapes = index.Query(point.EnvelopeInternal);

            IList<IGeometry> overlapTest = index.Query(shapes[0].EnvelopeInternal); // Envelope or EnvelopeInternal?

            // Now the app only have to test the intersection against a few shapes.
            int count = 0;
            foreach (IGeometry shape in nearShapes)
            {
                if (shape.Intersects(point))
                {
                    // Do whatever
                    count += 1;
                }
            }
        }

        public void MySqlGeo()
        {
            // https://community.tableau.com/thread/274727
            GeometryFactory factory = new GeometryFactory(new PrecisionModel(), 4326); //4326  SRID declaration
            Coordinate[] coordsSmall = new Coordinate[]{
                new Coordinate(-2,1),
                new Coordinate(0,1),
                new Coordinate(0,2),
                new Coordinate(-2,2),
                new Coordinate(-2,1) // Close this polygon!
			};
            var polySmall = (Polygon)factory.CreatePolygon(new LinearRing(coordsSmall));

            var container = new TestWrapper();
            container.geometry = polySmall;
            container.geometryStr = "";
            var cnn = Database.Helper.CreateConnection("aradadb");
            Database.Helper.CreateTable(cnn, container);
            int wait = 1;
            Database.Helper.Insert(cnn, container, -1);

            Database.Helper.CloseConnection(cnn);
        }
        public void CreateGeoJson()
        {
            System.Windows.Media.Media3D.Point3D[] Mesh = {
                new System.Windows.Media.Media3D.Point3D(0, 0, 0),
                new System.Windows.Media.Media3D.Point3D(0, 1, 0),
                new System.Windows.Media.Media3D.Point3D(1, 1, 0),
                new System.Windows.Media.Media3D.Point3D(1, 0, 0) };
            var json = new Objects.Json.GeoJson();

            json.type = "FeatureCollection";
            json.features.Add(new Objects.Json.Feature());
            json.features[0].type = "Feature";
            json.features[0].properties.name = "Building_Name_01";
            json.features[0].geometry.type = "Polygon";
            json.features[0].properties.type = "Building";
            json.features[0].geometry.coordinates = Objects.Json.ObjFunctions.MakePolygon(Mesh);

            classes.FileOutput.Json(json, "test");
        }
    }
}
