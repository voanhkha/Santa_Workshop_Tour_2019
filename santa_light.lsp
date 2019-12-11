/* Declares the optimization model. */
use io;

/* Reads instance data */
function input(){
	N_DAYS = 100;
	N_FAMILIES = 5000;
    local inFile = io.openRead("lsp_data/Npp.csv");
    FAMILY_SIZE[0..N_FAMILIES-1] = inFile.readInt();
	
	local inFile2 = io.openRead("lsp_data/Choice.csv");
	for[i in 0..N_FAMILIES-1]{
		for[j in 0..9]{
			FAMILY_CHOICES[i][j] = inFile2.readInt();
		}
	}	
}

function is_equal(a, b){
	if (a==b) return 1;
	else return 0;
}

function collectionContains(pref, a){
	flag = false;
	for[c in 0..9]{
		if (pref[c] == a) flag = true;
	}
	return flag;
}

function model() {
	x[i in 0..N_FAMILIES-1][c in 0..4] <- bool();
	for[d in 1..N_DAYS]{
		N[d] <- sum[i in 0..N_FAMILIES-1] (sum[c in 0..4] ( x[i][c]*is_equal(d, FAMILY_CHOICES[i][c])*FAMILY_SIZE[i] ) );
	}
	N[N_DAYS+1] <- N[N_DAYS];
	
	
	for[i in 0..N_FAMILIES-1]{
		constraint sum[c in 0..4] (x[i][c])==1;
	}
	
	for[d in 1..N_DAYS]{
		constraint N[d] >= 125;
		constraint N[d] <= 300;
	}
	
	for[i in 0..N_FAMILIES-1]{
		pref_[i] <- 50 * x[i][1]
					+ (50 + 9 * FAMILY_SIZE[i]) * x[i][2]
					+ (100 + 9 * FAMILY_SIZE[i]) * x[i][3]
					+ (200 + 9 * FAMILY_SIZE[i]) * x[i][4];
	}
	pref_ <- sum[i in 0..N_FAMILIES-1] (pref_[i]);
	accounting_penalty <- sum[d in 1..N_DAYS] ((N[d] - 125) / 400.0 * pow(N[d],0.5 + abs(N[d] - N[d+1]) / 50.0 ));
	minimize pref_ + accounting_penalty;
}

function param() {
    if(lsTimeLimit == nil) lsTimeLimit = 36000;
	
	local inputSub = io.openRead("subs_100/69111.csv");
	head = inputSub.readln();
	for[i in 0..N_FAMILIES-1]{
		line = inputSub.readln().split(",");
		d = line[1].toInt();
		for[c in 0..4]{
			if (FAMILY_CHOICES[i][c]==d) x[i][c].value = 1;
		}
	}
}

function output() {
    local solFile = io.openWrite("sol.csv");
    solFile.println("family_id,assigned_day");
    for[i in 0..N_FAMILIES-1]{
		for[c in 0..4]{
			if (x[i][c].value==1) {
				solFile.println(i + "," + FAMILY_CHOICES[i][c]);
			}
		} 
    }
}