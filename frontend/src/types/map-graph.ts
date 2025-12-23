export type LandCluster = {
    name: string;
    count: number;
}

export type LandData = {
    date: Date;
    lands : LandCluster[];
}