#include <algorithm>
#include <bits/stdc++.h>
#include <climits>
#include <random>
using namespace std;

#define fastIO ios::sync_with_stdio(false);cin.tie(NULL);cout.tie(NULL);cout.precision(numeric_limits<double>::max_digits10);

const int INF = INT_MAX;

struct PkgPosition {
    double x0, x1;
    double y0, y1;
    double z0, z1;
    PkgPosition(double x0, double x1, double y0, double y1, double z0, double z1)
        : x0(x0), x1(x1), y0(y0), y1(y1), z0(z0), z1(z1) {}
};

bool checkIntersection(const PkgPosition& pkg1, const PkgPosition& pkg2) {
    bool x_intersect = pkg1.x1 > pkg2.x0 && pkg2.x1 > pkg1.x0;
    bool y_intersect = pkg1.y1 > pkg2.y0 && pkg2.y1 > pkg1.y0;
    bool z_intersect = pkg1.z1 > pkg2.z0 && pkg2.z1 > pkg1.z0;
    return x_intersect && y_intersect && z_intersect;
}

// Structure to represent a package with dimensions, weight, and type
struct Package {
    int id;
    double length, width, height, weight;
    char type;  // 'P' for Priority, 'E' for Economy
    double extraCost;
    bool isPacked = false; // To check if the package is packed
    int uldID = -1; // ULD ID where the package is placed
    PkgPosition position = PkgPosition(-1, -1, -1, -1, -1, -1); // Coordinates

    Package(int id, double l, double w, double h, double wt, char t, double cost)
        : id(id), length(l), width(w), height(h), weight(wt), type(t), extraCost(cost) {}
};

// Structure to represent a ULD with dimensions, weight limit, and current load
struct ULD {
    int id;
    double length, width, height, maxWeight;
    double currentWeight;
    bool hasPriorityPackage = false; // To check if ULD contains Priority Package
    vector<vector<vector<bool>>> space; // 3D boolean vector
    vector<Package> packages;
    vector<PkgPosition> pkgPositions;
    // vector<vector<int>> z_min;

    ULD(int id, double l, double w, double h, double maxWt)
        : id(id), length(l), width(w), height(h), maxWeight(maxWt), currentWeight(0) {
            // z_min.assign(length, vector<int> (width, 0));
            space = vector<vector<vector<bool>>>(
            static_cast<int>(length),
            vector<vector<bool>>(
                static_cast<int>(width),
                vector<bool>(static_cast<int>(height), false)));

    }

    double volume() {
        return length * width * height;
    }

    // Check if there's enough space for a package
    bool hasEnoughSpace(const Package& pkg, int x, int y, int z) {
        if(space[x][y][z]) return false;
        PkgPosition p1 = PkgPosition(x, x + pkg.length - 1, y, y + pkg.width - 1, z, z + pkg.height - 1);
        int sz = pkgPositions.size();
        for(int i = sz - 1; i >=0 ; i--) {
            auto p2 = pkgPositions[i];
            if(checkIntersection(p1, p2)) return false; // Space is already occupied
        }
        return true;
    }

    // Mark space as occupied
    void occupySpace(Package& pkg, int x, int y, int z) {
        for (int i = x; i < x + pkg.length && i < length; ++i) {
            for (int j = y; j < y + pkg.width && j < width; ++j) {
                for (int k = z; k < z + pkg.height && k < height; ++k) {
                    space[i][j][k] = true;
                }
            }
        }

        // Update package's placement details
        pkg.isPacked = true;
        pkg.uldID = id;
        pkg.position.x0 = x;
        pkg.position.y0 = y;
        pkg.position.z0 = z;
        pkg.position.x1 = x + pkg.length - 1;
        pkg.position.y1 = y + pkg.width - 1;
        pkg.position.z1 = z + pkg.height - 1;

        pkgPositions.push_back(pkg.position);
        // for (int i = x; i < x + pkg.length; ++i) {
        //     for (int j = y; j < y + pkg.width; ++j) {
        //         if(z_min[x][y] >= z) {
        //             z_min[x][y] = max(z_min[x][y], z + (int)pkg.height);
        //         }
        //     }
        // }

        if (pkg.type == 'P') {
            hasPriorityPackage = true;
        }
    }
};

struct PackingDetails {
    int totalCost = INF;
    int totalPacked = 0;
    int priorityULDs = 0;
    vector<Package> packages;

    void printDeatils(string outputFileName) {
        // Write output to file
        ofstream outputFile(outputFileName);
        if (!outputFile.is_open()) {
            cerr << "Error: Could not open " << outputFileName << " for writing.\n";
            return;
        }

        outputFile << totalCost << "," << totalPacked << "," << priorityULDs << "\n";

        for (const auto& pkg : packages) {
            if (pkg.isPacked) {
                outputFile << pkg.id << "," << pkg.uldID << ","
                        << pkg.position.x0 << "," << pkg.position.y0 << "," << pkg.position.z0 << ","
                        << pkg.position.x1 << "," << pkg.position.y1 << "," << pkg.position.z1 << "\n";
            } else {
                outputFile << pkg.id << ",NONE,-1,-1,-1,-1,-1,-1\n";
            }
        }

        outputFile.close();
    }
} bestPacking;

// Function to check if a package fits into a ULD (considering weight and space)
bool fits(ULD& uld, Package& pkg) {
    if (pkg.weight + uld.currentWeight > uld.maxWeight) {
        return false; // Exceeds weight limit
    }

    // Check all possible positions for enough space
    for (int x = 0; x <= uld.length - pkg.length; ++x) {
        for (int y = 0; y <= uld.width - pkg.width; ++y) {
            for (int z = 0; z <= uld.height - pkg.height; ++z) {
                if (uld.hasEnoughSpace(pkg, x, y, z)) {
                    uld.occupySpace(pkg, x, y, z); // Mark space as occupied
                    uld.currentWeight += pkg.weight;
                    return true;
                }
            }
        }
    }

    return false; // No suitable space found
}

// Function to sort packages by different methods
void sortPackages(vector<Package>& packages, const string& method) {
    if (method == "extraCost") {
        // Priority first, then smallest extra cost
        sort(packages.begin(), packages.end(), [](const Package& a, const Package& b) {
            if (a.type != b.type) return a.type == 'P'; // Priority first
            return a.extraCost > b.extraCost; // largest extra cost
        });
    } else if (method == "weight") {
        // Priority first, then smallest weight
        sort(packages.begin(), packages.end(), [](const Package& a, const Package& b) {
            if (a.type != b.type) return a.type == 'P'; // Priority first
            return a.weight < b.weight; // Smallest weight
        });
    } else if (method == "volume") {
        // Priority first, then largest volume
        sort(packages.begin(), packages.end(), [](const Package& a, const Package& b) {
            if (a.type != b.type) return a.type == 'P'; // Priority first
            return (a.length * a.width * a.height) > (b.length * b.width * b.height); // Largest volume
        });
    }
}

// Function to compute results for a given sorting method
void computeResults(vector<Package> packages, vector<ULD> ulds, int P) {

    // Sort ULDs by volume
    sort(ulds.begin(), ulds.end(), [](ULD& a, ULD& b) {
        return a.volume() > b.volume();
    });

    // First-Fit Decreasing algorithm
    for (auto& pkg : packages) {
        for (auto& uld : ulds) {
            if (fits(uld, pkg)) {
                break; // Package packed
            }
        }
    }

    // Calculate statistics
    PackingDetails currPacking;
    currPacking.totalCost = 0;

    for (const auto& pkg : packages) {
        if (pkg.isPacked) {
            currPacking.totalPacked++;
        }
        else {
            if(pkg.type == 'P') {
                cerr << "Priority not packed\n";
                return;
            }
            currPacking.totalCost += pkg.extraCost; // Add cost for Economy packages
        }
    }

    for (const auto& uld : ulds) {
        if (uld.hasPriorityPackage) {
            currPacking.priorityULDs++;
        }
    }

    // Add penalty cost for spreading Priority Packages across multiple ULDs
    currPacking.totalCost += P * currPacking.priorityULDs;

    if(bestPacking.totalCost > currPacking.totalCost) {
        bestPacking = currPacking;
        bestPacking.packages = packages;
    }

    
}





int main() {
    fastIO;
    #ifndef ONLINE_JUDGE
    freopen("input.txt", "r" , stdin);
    freopen("output.txt", "w", stdout);
    #endif

    int N, M, P;// Number of ULDs, packages, penalty multiplier
    string input;
    getline(cin, input); // Read the entire line of input
    stringstream ss(input);
    string token;
    getline(ss, token, ',');
    N = stoi(token);
    getline(ss, token, ',');
    M = stoi(token);
    getline(ss, token, ',');
    P = stoi(token);

    vector<ULD> ulds;
    for (int i = 0; i < N; ++i) {
        string input;
        getline(cin, input); // Read the entire line of input
        stringstream ss(input);
        string token;

        getline(ss, token, ',');
        token = token.substr(1);
        int id = stoi(token);
        getline(ss, token, ',');
        double length = stod(token);
        getline(ss, token, ',');
        double width = stod(token);
        getline(ss, token, ',');
        double height = stod(token);
        getline(ss, token, ',');
        double maxWeight = stod(token);

        ulds.emplace_back(id, length, width, height, maxWeight);
    }

    vector<Package> packages;
    for (int i = 0; i < M; ++i) {
        string input;
        getline(cin, input); // Read the entire line of input
        stringstream ss(input);
        string token;

        getline(ss, token, ',');
        token = token.substr(2);
        int id = stoi(token);
        getline(ss, token, ',');
        double length = stod(token);
        getline(ss, token, ',');
        double width = stod(token);
        getline(ss, token, ',');
        double height = stod(token);
        getline(ss, token, ',');
        double weight = stod(token);
        getline(ss, token, ',');
        char type = token[0];
        getline(ss, token, ',');
        double extraCost = 0;
        if(type=='E') extraCost = stod(token);

        packages.emplace_back(id, length, width, height, weight, type, extraCost);
    }

    // Try all sorting methods
    sortPackages(packages, "extraCost");
    computeResults(packages, ulds, P);

    sortPackages(packages, "volume");
    computeResults(packages, ulds, P);

    sortPackages(packages, "weight");
    computeResults(packages, ulds, P);

    // double costMultiplier = 5.0 , wtMultiplier = 1.0, volMultiplier = 3.0;
    vector<Package> ppkgs, epkgs;
    for(auto& pkg: packages) {
        if(pkg.type == 'P') ppkgs.push_back(pkg);
        else epkgs.push_back(pkg);
    }
    for(int i=0; i < 10; i++) {
        shuffle(ppkgs.begin(), ppkgs.end(), default_random_engine(chrono::steady_clock::now().time_since_epoch().count()));
        shuffle(epkgs.begin(), epkgs.end(), default_random_engine(chrono::steady_clock::now().time_since_epoch().count()));

        packages = ppkgs;
        packages.insert(packages.end(), epkgs.begin(), epkgs.end());
        computeResults(packages, ulds, P);
    }


    bestPacking.printDeatils("output.txt");


    return 0;
}