import MapKit
import Observation
import SwiftUI

struct Location: Decodable {
    var lat: CLLocationDegrees
    var lon: CLLocationDegrees
}

@Observable
final class LocManagerViewModel {
    static let shared = LocManagerViewModel()
    private init() {}

    private(set) var location = Location(lat: 0.0, lon: 0.0)

    // the Map binds to this; no map is drawn until it has been set, so there is no default view
    var camera = MapCameraPosition.automatic
    private(set) var isPositioned = false

    func setLocation(lat: CLLocationDegrees, lon: CLLocationDegrees) {
        location.lat = lat
        location.lon = lon
    }

    // later location fixes only feed get_loc_auth, they never move the map
    func centerOnFirstFix(lat: CLLocationDegrees, lon: CLLocationDegrees) {
        guard !isPositioned else { return }
        camera = cityRegion(lat: lat, lon: lon)
        isPositioned = true
    }

    // animated so the map visibly flies to the city
    func recenter(lat: CLLocationDegrees, lon: CLLocationDegrees) {
        withAnimation(.easeInOut(duration: 2)) { camera = cityRegion(lat: lat, lon: lon) }
        isPositioned = true
    }

    // about 20 km across shows a whole city, which is what both callers want to see
    private func cityRegion(lat: CLLocationDegrees, lon: CLLocationDegrees) -> MapCameraPosition {
        .region(MKCoordinateRegion(center: CLLocationCoordinate2D(latitude: lat, longitude: lon),
                                   latitudinalMeters: 20_000, longitudinalMeters: 20_000))
    }
}

final class LocManager: NSObject, CLLocationManagerDelegate {
    static let shared = LocManager()
    private let locManager = CLLocationManager()

    override private init() {
        super.init()

        locManager.desiredAccuracy = kCLLocationAccuracyBest
        locManager.delegate = self
    }

    func startUpdates() {
        if locManager.authorizationStatus == .notDetermined {
            locManager.requestWhenInUseAuthorization()
        }

        Task {
            do {
                for try await update in CLLocationUpdate.liveUpdates() {
                    if let loc = update.location {
                        LocManagerViewModel.shared.setLocation(
                            lat: loc.coordinate.latitude,
                            lon: loc.coordinate.longitude)
                        LocManagerViewModel.shared.centerOnFirstFix(
                            lat: loc.coordinate.latitude,
                            lon: loc.coordinate.longitude)
                    }
                }
            } catch {
                print(error.localizedDescription)
            }
        }
    }
}
