import { createContext, useContext, useState } from 'react';

import MessageModel from '../models/Message.ts';


interface ArchivingContextType {
    selectedOrders: number[];
    // handleSelectedIds: (ids: number[]) => Promise<MessageModel>;
}


export const ArchivingContext = createContext<ArchivingContextType | null>(null);


export const DialogContextProvider = ({ children }: { children: React.ReactNode }) => {

    const [ selectedOrders, setSelectedOrders ] = useState<number[]>([]);

    return (
        <ArchivingContext.Provider value={ { selectedOrders, setSelectedOrders } }>
            {children}
        </ArchivingContext.Provider>
    );
};
